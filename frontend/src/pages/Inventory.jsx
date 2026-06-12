import React, { useEffect, useState } from "react";
import { Table, Card, Button, Form, Input, Modal, Select, Row, Col, Space, Typography, Tag, message, Descriptions } from "antd";
import { DatabaseOutlined, SyncOutlined, SwapOutlined, ThunderboltOutlined, SearchOutlined } from "@ant-design/icons";
import client from "../api/client";

const { Title, Text } = Typography;

const Inventory = () => {
  const [stock, setStock] = useState([]);
  const [loading, setLoading] = useState(false);
  const [warehouses, setWarehouses] = useState([]);
  const [locations, setLocations] = useState([]);
  const [products, setProducts] = useState([]);
  
  // Search state
  const [warehouseFilter, setWarehouseFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Modals
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState(false);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [isPredictModalOpen, setIsPredictModalOpen] = useState(false);
  
  const [predictionData, setPredictionData] = useState(null);
  const [predicting, setPredicting] = useState(false);

  const [adjustForm] = Form.useForm();
  const [transferForm] = Form.useForm();

  const loadStock = async () => {
    setLoading(true);
    try {
      const params = {};
      if (warehouseFilter) params.warehouse_id = warehouseFilter;
      const res = await client.get("/inventory/stock", { params });
      setStock(res.data);
    } catch (err) {
      message.error("Error al cargar stock");
    } finally {
      setLoading(false);
    }
  };

  const loadDropdowns = async () => {
    try {
      const [whRes, locRes, prodRes] = await Promise.all([
        client.get("/warehouses/"),
        client.get("/warehouses/locations/all"),
        client.get("/products/")
      ]);
      setWarehouses(whRes.data);
      setLocations(locRes.data);
      setProducts(prodRes.data);
      
      if (whRes.data.length > 0 && !warehouseFilter) {
        setWarehouseFilter(whRes.data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadDropdowns();
  }, []);

  useEffect(() => {
    if (warehouseFilter) {
      loadStock();
    }
  }, [warehouseFilter]);

  const handleAdjust = async (values) => {
    try {
      await client.post("/inventory/adjust", values);
      message.success("Ajuste de stock guardado correctamente");
      setIsAdjustModalOpen(false);
      adjustForm.resetFields();
      loadStock();
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al ajustar stock");
    }
  };

  const handleTransfer = async (values) => {
    try {
      await client.post("/inventory/transfer", values);
      message.success("Transferencia de stock completada");
      setIsTransferModalOpen(false);
      transferForm.resetFields();
      loadStock();
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al transferir stock");
    }
  };

  const handlePredict = async (productId) => {
    setPredicting(true);
    setPredictionData(null);
    setIsPredictModalOpen(true);
    try {
      const res = await client.get(`/inventory/predict/${productId}/${warehouseFilter}`);
      setPredictionData(res.data);
    } catch (err) {
      message.error("Error al generar predicción de demanda");
      setIsPredictModalOpen(false);
    } finally {
      setPredicting(false);
    }
  };

  const filteredStock = stock.filter(item => 
    item.product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.product.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.location.code.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <Title level={3} style={{ margin: 0, color: "#f8fafc" }}>Control de Stock en Tiempo Real</Title>
          <Text style={{ color: "#94a3b8" }}>Visualiza el inventario físico disponible en las ubicaciones, lotes y bodegas</Text>
        </div>
        <Space>
          <Select
            style={{ width: 200 }}
            placeholder="Seleccionar Bodega"
            value={warehouseFilter}
            onChange={setWarehouseFilter}
          >
            {warehouses.map(w => (
              <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
            ))}
          </Select>
          <Button icon={<SyncOutlined />} onClick={() => { loadStock(); message.success("Datos actualizados"); }} />
          <Button icon={<SwapOutlined />} onClick={() => setIsTransferModalOpen(true)}>
            Transferir
          </Button>
          <Button type="primary" icon={<DatabaseOutlined />} onClick={() => setIsAdjustModalOpen(true)}>
            Ajustar Stock (Audit)
          </Button>
        </Space>
      </div>

      <Card className="glass-panel" style={{ marginBottom: 16 }}>
        <Input
          placeholder="Buscar por SKU, Nombre o Ubicación..."
          prefix={<SearchOutlined />}
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "#fff" }}
        />
      </Card>

      <Card className="glass-panel" bodyStyle={{ padding: 0 }}>
        <Table
          loading={loading}
          dataSource={filteredStock}
          columns={[
            {
              title: "SKU",
              dataIndex: ["product", "sku"],
              key: "sku",
              render: text => <Text style={{ fontWeight: 600, color: "#00d4ff" }}>{text}</Text>
            },
            { title: "Nombre del Producto", dataIndex: ["product", "name"], key: "name" },
            { title: "Ubicación", dataIndex: ["location", "code"], key: "location" },
            {
              title: "Lote / Vencimiento",
              key: "lot",
              render: (_, record) => {
                if (!record.lot) return <Tag>N/A</Tag>;
                const expDate = record.lot.expiry_date ? new Date(record.lot.expiry_date).toLocaleDateString() : "Sin fecha";
                return (
                  <div>
                    <div><Tag color="cyan">{record.lot.lot_number}</Tag></div>
                    <small style={{ color: "#94a3b8" }}>Vence: {expDate}</small>
                  </div>
                );
              }
            },
            {
              title: "Total Físico",
              dataIndex: "quantity",
              key: "quantity",
              render: (qty, record) => `${qty} ${record.product.unit_of_measure}`
            },
            {
              title: "Reservado",
              dataIndex: "reserved_quantity",
              key: "reserved",
              render: (resQty, record) => (
                <span style={{ color: resQty > 0 ? "#f59e0b" : "#64748b" }}>
                  {resQty} {record.product.unit_of_measure}
                </span>
              )
            },
            {
              title: "Disponible",
              dataIndex: "available_quantity",
              key: "available",
              render: (availQty, record) => (
                <Text style={{ fontWeight: 700, color: availQty > 0 ? "#10b981" : "#ef4444" }}>
                  {availQty} {record.product.unit_of_measure}
                </Text>
              )
            },
            {
              title: "IA Forecasting",
              key: "ai",
              render: (_, record) => (
                <Button size="small" type="primary" ghost icon={<ThunderboltOutlined />} onClick={() => handlePredict(record.product_id)}>
                  Predecir Demanda
                </Button>
              )
            }
          ]}
          rowKey="id"
        />
      </Card>

      {/* Adjust Stock Modal */}
      <Modal title="Ajuste Manual de Stock" open={isAdjustModalOpen} onCancel={() => setIsAdjustModalOpen(false)} onOk={() => adjustForm.submit()}>
        <Form form={adjustForm} layout="vertical" onFinish={handleAdjust}>
          <Form.Item name="product_id" label="Producto" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="children">
              {products.map(p => (
                <Select.Option key={p.id} value={p.id}>{p.name} (SKU: {p.sku})</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="location_id" label="Ubicación Destino" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="children">
              {locations.map(l => (
                <Select.Option key={l.id} value={l.id}>{l.code}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="new_quantity" label="Nueva Cantidad Física" rules={[{ required: true }]}>
            <Input type="number" step="0.01" />
          </Form.Item>
          <Form.Item name="notes" label="Motivo del Ajuste" rules={[{ required: true }]}>
            <Input placeholder="Ej. Diferencia de inventario cíclico" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Transfer Stock Modal */}
      <Modal title="Transferencia Entre Ubicaciones" open={isTransferModalOpen} onCancel={() => setIsTransferModalOpen(false)} onOk={() => transferForm.submit()}>
        <Form form={transferForm} layout="vertical" onFinish={handleTransfer}>
          <Form.Item name="product_id" label="Producto" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="children">
              {products.map(p => (
                <Select.Option key={p.id} value={p.id}>{p.name} (SKU: {p.sku})</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Row gutter={8}>
            <Col span={12}>
              <Form.Item name="from_location_id" label="Ubicación Origen" rules={[{ required: true }]}>
                <Select showSearch optionFilterProp="children">
                  {locations.map(l => (
                    <Select.Option key={l.id} value={l.id}>{l.code}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="to_location_id" label="Ubicación Destino" rules={[{ required: true }]}>
                <Select showSearch optionFilterProp="children">
                  {locations.map(l => (
                    <Select.Option key={l.id} value={l.id}>{l.code}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="quantity" label="Cantidad a Transferir" rules={[{ required: true }]}>
            <Input type="number" step="0.01" />
          </Form.Item>
          <Form.Item name="notes" label="Notas de Transferencia">
            <Input placeholder="Reubicación por optimización de espacio" />
          </Form.Item>
        </Form>
      </Modal>

      {/* AI Demand Prediction Modal */}
      <Modal
        title="Predicción de Demanda Inteligente (IA)"
        open={isPredictModalOpen}
        onCancel={() => setIsPredictModalOpen(false)}
        footer={[
          <Button key="close" type="primary" onClick={() => setIsPredictModalOpen(false)}>Cerrar</Button>
        ]}
      >
        {predicting ? (
          <div style={{ textAlign: "center", padding: "40px 0" }}>
            <Spin tip="Ejecutando algoritmos predictivos..." />
          </div>
        ) : predictionData ? (
          <div>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Producto">{predictionData.product_name}</Descriptions.Item>
              <Descriptions.Item label="SKU">{predictionData.sku}</Descriptions.Item>
              <Descriptions.Item label="Stock Físico Actual">{predictionData.current_stock}</Descriptions.Item>
              <Descriptions.Item label="Consumo Diario Promedio">{predictionData.daily_average_consumption} uds</Descriptions.Item>
              <Descriptions.Item label="Demanda Proyectada (30 días)">{predictionData.predicted_demand_next_30_days} uds</Descriptions.Item>
              <Descriptions.Item label="Días de Stock Estimados">{predictionData.estimated_days_of_stock} días</Descriptions.Item>
              <Descriptions.Item label="Sugerencia de Reabastecimiento">
                <Text style={{ fontWeight: 700, color: "#1890ff" }}>
                  {predictionData.recommended_reorder_qty} unidades
                </Text>
              </Descriptions.Item>
            </Descriptions>
            
            {predictionData.risk_of_stockout ? (
              <Alert
                message="Riesgo de Quiebre Detectado"
                description="El stock actual se agotará antes del término del período de 30 días si continúa el consumo promedio."
                type="error"
                showIcon
                style={{ marginTop: 16 }}
              />
            ) : (
              <Alert
                message="Stock Saludable"
                description="Los niveles actuales de inventario son suficientes para cubrir la demanda proyectada."
                type="success"
                showIcon
                style={{ marginTop: 16 }}
              />
            )}
          </div>
        ) : (
          <div style={{ color: "#ef4444" }}>No se pudo generar el análisis.</div>
        )}
      </Modal>
    </div>
  );
};

export default Inventory;
