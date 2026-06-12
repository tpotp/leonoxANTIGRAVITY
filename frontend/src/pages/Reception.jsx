import React, { useEffect, useState } from "react";
import { Table, Card, Button, Form, Input, Modal, Select, Row, Col, Space, Typography, Tag, message, DatePicker, List } from "antd";
import { PlusOutlined, DownloadOutlined, CheckOutlined, EditOutlined, ShoppingCartOutlined } from "@ant-design/icons";
import client from "../api/client";

const { Title, Text } = Typography;

const Reception = () => {
  const [receptions, setReceptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [warehouses, setWarehouses] = useState([]);
  const [products, setProducts] = useState([]);
  const [locations, setLocations] = useState([]);

  // Active Reception view
  const [activeRep, setActiveRep] = useState(null);

  // Modals
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [isLineModalOpen, setIsLineModalOpen] = useState(false);
  
  const [newRepForm] = Form.useForm();
  const [lineForm] = Form.useForm();
  
  const [newRepItems, setNewRepItems] = useState([]);
  const [activeLine, setActiveLine] = useState(null);

  const loadReceptions = async () => {
    setLoading(true);
    try {
      const res = await client.get("/reception/");
      setReceptions(res.data);
    } catch (err) {
      message.error("Error al cargar recepciones");
    } finally {
      setLoading(false);
    }
  };

  const loadDropdowns = async () => {
    try {
      const [whRes, prodRes, locRes] = await Promise.all([
        client.get("/warehouses/"),
        client.get("/products/"),
        client.get("/warehouses/locations/all")
      ]);
      setWarehouses(whRes.data);
      setProducts(prodRes.data);
      setLocations(locRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadReceptions();
    loadDropdowns();
  }, []);

  const handleCreateReception = async (values) => {
    if (newRepItems.length === 0) {
      message.error("Debes agregar al menos un producto a la recepción");
      return;
    }
    
    try {
      const payload = {
        warehouse_id: values.warehouse_id,
        supplier_name: values.supplier_name,
        expected_date: values.expected_date?.toISOString(),
        notes: values.notes,
        lines: newRepItems.map(item => ({
          product_id: item.product_id,
          expected_quantity: item.expected_quantity
        }))
      };
      
      await client.post("/reception/", payload);
      message.success("Recepción registrada correctamente (Borrador)");
      setIsNewModalOpen(false);
      newRepForm.resetFields();
      setNewRepItems([]);
      loadReceptions();
    } catch (err) {
      message.error("Error al crear recepción");
    }
  };

  const handleAddItemToNewRep = (values) => {
    const prod = products.find(p => p.id === values.product_id);
    if (!prod) return;
    
    setNewRepItems(prev => [
      ...prev,
      {
        product_id: prod.id,
        sku: prod.sku,
        name: prod.name,
        expected_quantity: parseFloat(values.expected_quantity)
      }
    ]);
  };

  const handleSelectReception = async (record) => {
    try {
      const res = await client.get(`/reception/${record.id}`);
      setActiveRep(res.data);
    } catch (err) {
      message.error("Error al cargar detalles de la recepción");
    }
  };

  const handleOpenReceiveLine = (line) => {
    setActiveLine(line);
    lineForm.setFieldsValue({
      received_quantity: line.expected_quantity,
      location_id: line.location_id
    });
    setIsLineModalOpen(true);
  };

  const handleSaveLineReceival = async (values) => {
    try {
      // 1. Create Lot in database if batch info is supplied
      let lotId = null;
      if (values.lot_number) {
        const lotRes = await client.post("/inventory/stock/lot", {
          product_id: activeLine.product_id,
          lot_number: values.lot_number,
          manufacture_date: values.manufacture_date?.toISOString(),
          expiry_date: values.expiry_date?.toISOString(),
          supplier: activeRep.supplier_name
        });
        lotId = lotRes.data.id;
      }
      
      // 2. Update line receival quantities and storage location
      await client.put(`/reception/lines/${activeLine.id}`, {
        received_quantity: parseFloat(values.received_quantity),
        location_id: values.location_id,
        lot_id: lotId,
        notes: values.notes
      });
      
      message.success("Línea guardada localmente");
      setIsLineModalOpen(false);
      lineForm.resetFields();
      
      // Reload details
      handleSelectReception(activeRep);
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al actualizar línea");
    }
  };

  const handleConfirmReception = async () => {
    try {
      await client.post(`/reception/${activeRep.id}/confirm`);
      message.success("¡Recepción confirmada e inventario ingresado con éxito!");
      setActiveRep(null);
      loadReceptions();
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al confirmar recepción");
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <Title level={3} style={{ margin: 0, color: "#f8fafc" }}>Recepción de Mercaderías</Title>
          <Text style={{ color: "#94a3b8" }}>Ingresa productos al inventario vinculando lotes, vencimientos y ubicaciones</Text>
        </div>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsNewModalOpen(true)}>
            Nueva Recepción
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        {/* Reception List */}
        <Col xs={24} lg={12}>
          <Card title="Recepciones de Compra" className="glass-panel" bodyStyle={{ padding: 0 }}>
            <Table
              loading={loading}
              dataSource={receptions}
              columns={[
                { title: "Referencia", dataIndex: "reference_number", key: "ref" },
                { title: "Proveedor", dataIndex: "supplier_name", key: "supplier" },
                {
                  title: "Estado",
                  dataIndex: "status",
                  key: "status",
                  render: status => {
                    const color = status === "COMPLETED" ? "success" : status === "IN_PROGRESS" ? "processing" : "default";
                    return <Tag color={color}>{status}</Tag>;
                  }
                },
                {
                  title: "Acciones",
                  key: "actions",
                  render: (_, record) => (
                    <Button size="small" onClick={() => handleSelectReception(record)}>
                      Gestionar
                    </Button>
                  )
                }
              ]}
              rowKey="id"
            />
          </Card>
        </Col>

        {/* Detailed Reception Management Panel */}
        <Col xs={24} lg={12}>
          {activeRep ? (
            <Card
              title={`Gestionar Recepción: ${activeRep.reference_number}`}
              className="glass-panel"
              extra={
                activeRep.status !== "COMPLETED" && (
                  <Button type="primary" icon={<CheckOutlined />} onClick={handleConfirmReception}>
                    Confirmar Ingreso Físico
                  </Button>
                )
              }
            >
              <DescriptionsItem label="Proveedor" value={activeRep.supplier_name} />
              <DescriptionsItem label="Notas" value={activeRep.notes || "Sin notas"} />
              <DescriptionsItem label="Estado" value={<Tag>{activeRep.status}</Tag>} />

              <div style={{ marginTop: 24, marginBottom: 12, fontWeight: 600 }}>Líneas de Detalle</div>
              <Table
                dataSource={activeRep.lines}
                size="small"
                pagination={false}
                columns={[
                  { title: "Producto", dataIndex: ["product", "sku"], key: "product" },
                  { title: "Esperado", dataIndex: "expected_quantity", key: "expected" },
                  { title: "Recibido", dataIndex: "received_quantity", key: "received" },
                  {
                    title: "Ubicación",
                    key: "loc",
                    render: (_, record) => record.location?.code || <Text type="secondary">No Asignada</Text>
                  },
                  {
                    title: "Acción",
                    key: "action",
                    render: (_, record) => (
                      <Button
                        size="small"
                        icon={<EditOutlined />}
                        disabled={activeRep.status === "COMPLETED"}
                        onClick={() => handleOpenReceiveLine(record)}
                      >
                        Recibir
                      </Button>
                    )
                  }
                ]}
                rowKey="id"
              />
            </Card>
          ) : (
            <Card className="glass-panel" style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <div style={{ textAlign: "center", padding: "40px 0", color: "#64748b" }}>
                <DownloadOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>Selecciona una recepción del listado para gestionar el ingreso físico a racks</div>
              </div>
            </Card>
          )}
        </Col>
      </Row>

      {/* New Reception Modal */}
      <Modal title="Crear Orden de Recepción" open={isNewModalOpen} onCancel={() => setIsNewModalOpen(false)} onOk={() => newRepForm.submit()} width={720}>
        <Form form={newRepForm} layout="vertical" onFinish={handleCreateReception}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="warehouse_id" label="Bodega de Destino" rules={[{ required: true }]}>
                <Select>
                  {warehouses.map(w => (
                    <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="supplier_name" label="Proveedor" rules={[{ required: true }]}>
                <Input placeholder="Ej. Distribuidora Central S.A." />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="expected_date" label="Fecha Estimada de Llegada">
                <DatePicker showTime style={{ width: "100%" }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="notes" label="Notas">
                <Input />
              </Form.Item>
            </Col>
          </Row>

          <Card title="Agregar Productos a Recepción" size="small" style={{ marginTop: 16 }}>
            <Form layout="inline" onFinish={handleAddItemToNewRep}>
              <Form.Item name="product_id" rules={[{ required: true }]} style={{ width: "60%" }}>
                <Select placeholder="Seleccionar SKU" showSearch optionFilterProp="children">
                  {products.map(p => (
                    <Select.Option key={p.id} value={p.id}>{p.name} (SKU: {p.sku})</Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="expected_quantity" rules={[{ required: true }]} style={{ width: "25%" }}>
                <Input type="number" placeholder="Cant." />
              </Form.Item>
              <Form.Item style={{ width: "10%" }}>
                <Button type="primary" htmlType="submit" icon={<PlusOutlined />} />
              </Form.Item>
            </Form>
            <List
              style={{ marginTop: 12, maxHeight: 150, overflowY: "auto" }}
              size="small"
              dataSource={newRepItems}
              renderItem={item => (
                <List.Item>
                  <Text>{item.name} (SKU: {item.sku})</Text>
                  <Tag color="blue">{item.expected_quantity} unidades</Tag>
                </List.Item>
              )}
            />
          </Card>
        </Form>
      </Modal>

      {/* Receive Line Details Modal */}
      <Modal title="Chequeo Físico de Línea" open={isLineModalOpen} onCancel={() => setIsLineModalOpen(false)} onOk={() => lineForm.submit()}>
        <Form form={lineForm} layout="vertical" onFinish={handleSaveLineReceival}>
          <Form.Item name="received_quantity" label="Cantidad Recibida Conforme" rules={[{ required: true }]}>
            <Input type="number" step="0.01" />
          </Form.Item>
          <Form.Item name="location_id" label="Ubicación Almacenamiento (Rack)" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="children">
              {locations.map(l => (
                <Select.Option key={l.id} value={l.id}>{l.code}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          
          <Card title="Información de Lote / Vencimiento (Trazabilidad)" size="small" style={{ marginBottom: 16 }}>
            <Form.Item name="lot_number" label="Número de Lote">
              <Input placeholder="Ej. LOT-2026A" />
            </Form.Item>
            <Row gutter={8}>
              <Col span={12}>
                <Form.Item name="manufacture_date" label="Fecha Elaboración">
                  <DatePicker style={{ width: "100%" }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="expiry_date" label="Fecha Vencimiento">
                  <DatePicker style={{ width: "100%" }} />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          <Form.Item name="notes" label="Notas / Discrepancias">
            <Input placeholder="Diferencia de mercadería mojada o dañada" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

const DescriptionsItem = ({ label, value }) => (
  <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
    <span style={{ color: "#94a3b8" }}>{label}</span>
    <span style={{ color: "#f8fafc", fontWeight: 500 }}>{value}</span>
  </div>
);

export default Reception;
