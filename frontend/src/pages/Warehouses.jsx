import React, { useEffect, useState } from "react";
import { Table, Card, Button, Form, Input, Modal, Select, Row, Col, Space, Typography, Tag, message } from "antd";
import { HomeOutlined, PlusOutlined, EnvironmentOutlined } from "@ant-design/icons";
import client from "../api/client";

const { Title, Text } = Typography;

const Warehouses = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWh, setSelectedWh] = useState(null);
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [locations, setLocations] = useState([]);
  
  // Modals
  const [isWhModalOpen, setIsWhModalOpen] = useState(false);
  const [isZoneModalOpen, setIsZoneModalOpen] = useState(false);
  const [isLocModalOpen, setIsLocModalOpen] = useState(false);

  const [whForm] = Form.useForm();
  const [zoneForm] = Form.useForm();
  const [locForm] = Form.useForm();

  const loadWarehouses = async () => {
    try {
      const res = await client.get("/warehouses/");
      setWarehouses(res.data);
      if (res.data.length > 0 && !selectedWh) {
        setSelectedWh(res.data[0]);
      }
    } catch (err) {
      message.error("Error al cargar bodegas");
    }
  };

  const loadZones = async (whId) => {
    try {
      const res = await client.get(`/warehouses/${whId}/zones`);
      setZones(res.data);
      if (res.data.length > 0) {
        setSelectedZone(res.data[0]);
      } else {
        setSelectedZone(null);
        setLocations([]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadLocations = async (zoneId) => {
    try {
      const res = await client.get(`/warehouses/zones/${zoneId}/locations`);
      setLocations(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadWarehouses();
  }, []);

  useEffect(() => {
    if (selectedWh) {
      loadZones(selectedWh.id);
    }
  }, [selectedWh]);

  useEffect(() => {
    if (selectedZone) {
      loadLocations(selectedZone.id);
    } else {
      setLocations([]);
    }
  }, [selectedZone]);

  const handleCreateWh = async (values) => {
    try {
      await client.post("/warehouses/", values);
      message.success("Bodega creada correctamente");
      setIsWhModalOpen(false);
      whForm.resetFields();
      loadWarehouses();
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al crear bodega");
    }
  };

  const handleCreateZone = async (values) => {
    try {
      await client.post("/warehouses/zones", { ...values, warehouse_id: selectedWh.id });
      message.success("Zona creada correctamente");
      setIsZoneModalOpen(false);
      zoneForm.resetFields();
      loadZones(selectedWh.id);
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al crear zona");
    }
  };

  const handleCreateLoc = async (values) => {
    try {
      await client.post("/warehouses/locations", {
        ...values,
        warehouse_id: selectedWh.id,
        zone_id: selectedZone.id
      });
      message.success("Ubicación creada correctamente");
      setIsLocModalOpen(false);
      locForm.resetFields();
      loadLocations(selectedZone.id);
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al crear ubicación");
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <Title level={3} style={{ margin: 0, color: "#f8fafc" }}>Estructura de Almacenes</Title>
          <Text style={{ color: "#94a3b8" }}>Configura tus centros de distribución, zonas y ubicaciones de racks</Text>
        </div>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsWhModalOpen(true)}>
            Nueva Bodega
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        {/* Warehouses list */}
        <Col xs={24} md={8}>
          <Card title="Bodegas" className="glass-panel">
            <ListGrid
              data={warehouses}
              selectedId={selectedWh?.id}
              onSelect={setSelectedWh}
              titleField="name"
              subField="code"
              extraField="city"
            />
          </Card>
        </Col>

        {/* Zones list */}
        <Col xs={24} md={8}>
          <Card
            title="Zonas"
            className="glass-panel"
            extra={
              selectedWh && (
                <Button size="small" type="link" icon={<PlusOutlined />} onClick={() => setIsZoneModalOpen(true)}>
                  Agregar
                </Button>
              )
            }
          >
            <ListGrid
              data={zones}
              selectedId={selectedZone?.id}
              onSelect={setSelectedZone}
              titleField="name"
              subField="code"
              extraField="zone_type"
              isTag={true}
            />
          </Card>
        </Col>

        {/* Locations list */}
        <Col xs={24} md={8}>
          <Card
            title="Ubicaciones (Rack)"
            className="glass-panel"
            extra={
              selectedZone && (
                <Button size="small" type="link" icon={<PlusOutlined />} onClick={() => setIsLocModalOpen(true)}>
                  Agregar
                </Button>
              )
            }
          >
            <Table
              dataSource={locations}
              columns={[
                { title: "Código", dataIndex: "code", key: "code" },
                { title: "Pasillo", dataIndex: "aisle", key: "aisle" },
                { title: "Nivel", dataIndex: "level", key: "level" },
                {
                  title: "Capacidad (kg)",
                  dataIndex: "max_weight",
                  key: "max_weight",
                  render: val => `${val} kg`
                }
              ]}
              rowKey="id"
              pagination={{ pageSize: 6 }}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {/* WH Modal */}
      <Modal title="Crear Nueva Bodega" open={isWhModalOpen} onCancel={() => setIsWhModalOpen(false)} onOk={() => whForm.submit()}>
        <Form form={whForm} layout="vertical" onFinish={handleCreateWh}>
          <Form.Item name="name" label="Nombre de Bodega" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="code" label="Código Unico (ej. B-CENTRAL)" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="address" label="Dirección">
            <Input />
          </Form.Item>
          <Row gutter={8}>
            <Col span={12}>
              <Form.Item name="city" label="Ciudad">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="country" label="País">
                <Input />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Zone Modal */}
      <Modal title="Crear Nueva Zona" open={isZoneModalOpen} onCancel={() => setIsZoneModalOpen(false)} onOk={() => zoneForm.submit()}>
        <Form form={zoneForm} layout="vertical" onFinish={handleCreateZone}>
          <Form.Item name="name" label="Nombre de Zona" rules={[{ required: true }]}>
            <Input placeholder="Ej. Estantería Principal" />
          </Form.Item>
          <Form.Item name="code" label="Código" rules={[{ required: true }]}>
            <Input placeholder="Ej. Z-STO" />
          </Form.Item>
          <Form.Item name="zone_type" label="Tipo de Zona" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="RECEIVING">Recepción (Ingreso)</Select.Option>
              <Select.Option value="STORAGE">Almacenamiento</Select.Option>
              <Select.Option value="PICKING">Picking (Preparación)</Select.Option>
              <Select.Option value="DISPATCH">Despacho (Salida)</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Location Modal */}
      <Modal title="Crear Nueva Ubicación (Rack)" open={isLocModalOpen} onCancel={() => setIsLocModalOpen(false)} onOk={() => locForm.submit()}>
        <Form form={locForm} layout="vertical" onFinish={handleCreateLoc}>
          <Form.Item name="code" label="Código de Ubicación" rules={[{ required: true }]} help="Formato estándar sugerido: LOC-PASILLO-ESTANTE-NIVEL-POSICION">
            <Input placeholder="Ej. LOC-A-01-01-01" />
          </Form.Item>
          <Row gutter={8}>
            <Col span={6}>
              <Form.Item name="aisle" label="Pasillo">
                <Input placeholder="A" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="rack" label="Estante">
                <Input placeholder="01" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="level" label="Nivel">
                <Input placeholder="01" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="position" label="Posición">
                <Input placeholder="01" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={8}>
            <Col span={12}>
              <Form.Item name="max_weight" label="Peso Máximo (kg)" initialValue={1000.0}>
                <Input type="number" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="max_volume" label="Volumen Máximo (m3)" initialValue={10.0}>
                <Input type="number" step="0.1" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

// Helper List Grid
const ListGrid = ({ data, selectedId, onSelect, titleField, subField, extraField, isTag = false }) => {
  return (
    <div style={{ maxHeight: 400, overflowY: "auto" }}>
      {data.map(item => {
        const isSelected = item.id === selectedId;
        return (
          <div
            key={item.id}
            onClick={() => onSelect(item)}
            style={{
              padding: "12px 16px",
              borderRadius: 8,
              cursor: "pointer",
              marginBottom: 8,
              background: isSelected ? "rgba(24,144,255,0.12)" : "rgba(255,255,255,0.02)",
              border: isSelected ? "1px solid #1890ff" : "1px solid rgba(255,255,255,0.05)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              transition: "all 0.2s"
            }}
          >
            <div>
              <div style={{ fontWeight: 600, color: isSelected ? "#00d4ff" : "#f8fafc" }}>
                {item[titleField]}
              </div>
              <div style={{ fontSize: 12, color: "#64748b" }}>Código: {item[subField]}</div>
            </div>
            {isTag ? (
              <Tag color="blue">{item[extraField]}</Tag>
            ) : (
              <span style={{ fontSize: 12, color: "#94a3b8" }}>{item[extraField]}</span>
            )}
          </div>
        );
      })}
      {data.length === 0 && (
        <div style={{ textAlign: "center", padding: "24px 0", color: "#64748b" }}>
          Sin datos cargados
        </div>
      )}
    </div>
  );
};

export default Warehouses;
