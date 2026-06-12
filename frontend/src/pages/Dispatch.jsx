import React, { useEffect, useState } from "react";
import { Table, Card, Button, Form, Input, Modal, Select, Row, Col, Space, Typography, Tag, message } from "antd";
import { UploadOutlined, PlusOutlined, CheckCircleOutlined, CarOutlined } from "@ant-design/icons";
import client from "../api/client";

const { Title, Text } = Typography;

const Dispatch = () => {
  const [dispatches, setDispatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [warehouses, setWarehouses] = useState([]);
  const [pickedOrders, setPickedOrders] = useState([]);

  // Modals
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  
  const [newDispatchForm] = Form.useForm();

  const loadDispatches = async () => {
    setLoading(true);
    try {
      const res = await client.get("/dispatch/");
      setDispatches(res.data);
    } catch (err) {
      message.error("Error al cargar despachos");
    } finally {
      setLoading(false);
    }
  };

  const loadDropdowns = async () => {
    try {
      const [whRes, orderRes] = await Promise.all([
        client.get("/warehouses/"),
        client.get("/orders/")
      ]);
      setWarehouses(whRes.data);
      // Filter orders that are COMPLETED (picked) but not yet DISPATCHED
      setPickedOrders(orderRes.data.filter(o => o.status === "COMPLETED"));
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadDispatches();
    loadDropdowns();
  }, []);

  const handleCreateDispatch = async (values) => {
    try {
      await client.post("/dispatch/", values);
      message.success("Despacho registrado correctamente (Listo para carga)");
      setIsNewModalOpen(false);
      newDispatchForm.resetFields();
      loadDispatches();
      loadDropdowns();
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al crear despacho");
    }
  };

  const handleConfirmDispatch = async (id) => {
    try {
      await client.post(`/dispatch/${id}/confirm`);
      message.success("¡Despacho liberado y rebajado del stock físico!");
      loadDispatches();
      loadDropdowns();
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al confirmar despacho");
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <Title level={3} style={{ margin: 0, color: "#f8fafc" }}>Despacho y Salidas</Title>
          <Text style={{ color: "#94a3b8" }}>Consolida pedidos preparados, asigna transportistas y realiza la salida fiscal de stock</Text>
        </div>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsNewModalOpen(true)}>
            Consolidar Salida
          </Button>
        </Space>
      </div>

      <Card className="glass-panel" bodyStyle={{ padding: 0 }}>
        <Table
          loading={loading}
          dataSource={dispatches}
          columns={[
            { title: "Nº Despacho", dataIndex: "dispatch_number", key: "num" },
            {
              title: "Transportista",
              key: "carrier",
              render: (_, record) => record.carrier ? `${record.carrier} (${record.tracking_number || "Sin Tracking"})` : "N/A"
            },
            {
              title: "Estado",
              dataIndex: "status",
              key: "status",
              render: s => {
                const colors = { DISPATCHED: "success", PENDING: "processing", CANCELLED: "error" };
                return <Tag color={colors[s] || "default"}>{s}</Tag>;
              }
            },
            {
              title: "Fecha Despacho",
              dataIndex: "dispatched_at",
              key: "date",
              render: date => date ? new Date(date).toLocaleString() : "Pendiente"
            },
            {
              title: "Acciones",
              key: "actions",
              render: (_, record) => (
                <Button
                  size="small"
                  type="primary"
                  icon={<CarOutlined />}
                  disabled={record.status === "DISPATCHED"}
                  onClick={() => handleConfirmDispatch(record.id)}
                >
                  Liberar Despacho
                </Button>
              )
            }
          ]}
          rowKey="id"
        />
      </Card>

      {/* New Dispatch Modal */}
      <Modal title="Consolidar Pedidos y Crear Despacho" open={isNewModalOpen} onCancel={() => setIsNewModalOpen(false)} onOk={() => newDispatchForm.submit()}>
        <Form form={newDispatchForm} layout="vertical" onFinish={handleCreateDispatch}>
          <Form.Item name="warehouse_id" label="Bodega de Origen" rules={[{ required: true }]}>
            <Select>
              {warehouses.map(w => (
                <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="order_ids" label="Pedidos Preparados (Completados)" rules={[{ required: true, type: "array" }]}>
            <Select mode="multiple" placeholder="Seleccionar Pedidos">
              {pickedOrders.map(o => (
                <Select.Option key={o.id} value={o.id}>{o.order_number} — Cliente: {o.customer_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={8}>
            <Col span={12}>
              <Form.Item name="carrier" label="Transportista / Courier">
                <Input placeholder="Ej. Chilexpress / Fedex" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="tracking_number" label="Nº de Seguimiento">
                <Input placeholder="Ej. 928392109" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="Notas de Despacho">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Dispatch;
