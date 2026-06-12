import React, { useEffect, useState } from "react";
import { Table, Card, Button, Form, Input, Modal, Select, Row, Col, Space, Typography, Tag, message, List } from "antd";
import { InboxOutlined, PlusOutlined, UserOutlined, CheckCircleOutlined, ThunderboltOutlined, EnvironmentOutlined } from "@ant-design/icons";
import client from "../api/client";
import useAuthStore from "../stores/authStore";

const { Title, Text } = Typography;

const Orders = () => {
  const { user } = useAuthStore();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [warehouses, setWarehouses] = useState([]);
  const [products, setProducts] = useState([]);
  const [operators, setOperators] = useState([]);
  
  // Active states
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [pickingTasks, setPickingTasks] = useState([]);
  const [operatorTasks, setOperatorTasks] = useState([]);

  // Modals
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [isPickModalOpen, setIsPickModalOpen] = useState(false);
  
  const [newOrderForm] = Form.useForm();
  const [assignForm] = Form.useForm();
  const [pickForm] = Form.useForm();

  const [newOrderItems, setNewOrderItems] = useState([]);
  const [activeTask, setActiveTask] = useState(null);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const res = await client.get("/orders/");
      setOrders(res.data);
    } catch (err) {
      message.error("Error al cargar pedidos");
    } finally {
      setLoading(false);
    }
  };

  const loadOperatorTasks = async () => {
    if (!user) return;
    try {
      const res = await client.get(`/orders/picking-tasks/operator/${user.id}`);
      setOperatorTasks(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadDropdowns = async () => {
    try {
      const [whRes, prodRes, userRes] = await Promise.all([
        client.get("/warehouses/"),
        client.get("/products/"),
        client.get("/users/")
      ]);
      setWarehouses(whRes.data);
      setProducts(prodRes.data);
      // Filter users who can do picking tasks (all supervisors and operators)
      setOperators(userRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadOrders();
    loadDropdowns();
  }, []);

  useEffect(() => {
    if (user) {
      loadOperatorTasks();
    }
  }, [user]);

  const handleCreateOrder = async (values) => {
    if (newOrderItems.length === 0) {
      message.error("Debes agregar al menos un SKU al pedido");
      return;
    }
    try {
      const payload = {
        warehouse_id: values.warehouse_id,
        order_type: values.order_type || "SALES",
        customer_name: values.customer_name,
        priority: values.priority || "MEDIUM",
        notes: values.notes,
        lines: newOrderItems.map(item => ({
          product_id: item.product_id,
          requested_quantity: item.requested_quantity
        }))
      };
      await client.post("/orders/", payload);
      message.success("Pedido registrado con éxito (Pendiente)");
      setIsNewModalOpen(false);
      newOrderForm.resetFields();
      setNewOrderItems([]);
      loadOrders();
    } catch (err) {
      message.error("Error al registrar pedido");
    }
  };

  const handleAddItemToNewOrder = (values) => {
    const prod = products.find(p => p.id === values.product_id);
    if (!prod) return;
    setNewOrderItems(prev => [
      ...prev,
      {
        product_id: prod.id,
        sku: prod.sku,
        name: prod.name,
        requested_quantity: parseFloat(values.requested_quantity)
      }
    ]);
  };

  const handleSelectOrder = async (record) => {
    try {
      const res = await client.get(`/orders/${record.id}`);
      setSelectedOrder(res.data);
      
      // Extract active tasks
      const tasks = [];
      res.data.lines.forEach(l => {
        if (l.picking_tasks) {
          tasks.push(...l.picking_tasks);
        }
      });
      setPickingTasks(tasks);
    } catch (err) {
      message.error("Error al cargar detalle del pedido");
    }
  };

  const handleAssignOrder = async (values) => {
    try {
      await client.post(`/orders/${selectedOrder.id}/assign?operator_id=${values.operator_id}&strategy=${values.strategy}`);
      message.success("Pedido asignado y stock reservado mediante algoritmo logístico");
      setIsAssignModalOpen(false);
      assignForm.resetFields();
      handleSelectOrder(selectedOrder);
      loadOrders();
      loadOperatorTasks();
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al asignar pedido");
    }
  };

  const handleOpenPickTask = (task) => {
    setActiveTask(task);
    pickForm.setFieldsValue({ picked_quantity: task.quantity_to_pick });
    setIsPickModalOpen(true);
  };

  const handleExecutePick = async (values) => {
    try {
      await client.post(`/orders/picking-tasks/${activeTask.id}/execute`, {
        picked_quantity: parseFloat(values.picked_quantity)
      });
      message.success("Pick registrado correctamente");
      setIsPickModalOpen(false);
      pickForm.resetFields();
      loadOperatorTasks();
      loadOrders();
      if (selectedOrder) {
        handleSelectOrder(selectedOrder);
      }
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al procesar pick");
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <Title level={3} style={{ margin: 0, color: "#f8fafc" }}>Preparación de Pedidos (Picking)</Title>
          <Text style={{ color: "#94a3b8" }}>Planifica y ejecuta el picking de mercaderías para despachos y traslados</Text>
        </div>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsNewModalOpen(true)}>
            Nuevo Pedido
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* Orders list */}
        <Col xs={24} lg={12}>
          <Card title="Pedidos Registrados" className="glass-panel" bodyStyle={{ padding: 0 }}>
            <Table
              loading={loading}
              dataSource={orders}
              columns={[
                { title: "Nº Pedido", dataIndex: "order_number", key: "num" },
                { title: "Cliente / Destino", dataIndex: "customer_name", key: "customer" },
                {
                  title: "Prioridad",
                  dataIndex: "priority",
                  key: "priority",
                  render: p => {
                    const colors = { URGENT: "red", HIGH: "orange", MEDIUM: "blue", LOW: "default" };
                    return <Tag color={colors[p] || "blue"}>{p}</Tag>;
                  }
                },
                {
                  title: "Estado",
                  dataIndex: "status",
                  key: "status",
                  render: s => {
                    const colors = { COMPLETED: "success", ASSIGNED: "processing", DISPATCHED: "cyan", PENDING: "default" };
                    return <Tag color={colors[s] || "default"}>{s}</Tag>;
                  }
                },
                {
                  title: "Acciones",
                  key: "actions",
                  render: (_, record) => (
                    <Button size="small" onClick={() => handleSelectOrder(record)}>
                      Ver Detalle
                    </Button>
                  )
                }
              ]}
              rowKey="id"
            />
          </Card>
        </Col>

        {/* Selected Order Detailed View */}
        <Col xs={24} lg={12}>
          {selectedOrder ? (
            <Card
              title={`Pedido: ${selectedOrder.order_number}`}
              className="glass-panel"
              extra={
                selectedOrder.status === "PENDING" && (
                  <Button type="primary" icon={<ThunderboltOutlined />} onClick={() => setIsAssignModalOpen(true)}>
                    Asignar Picking
                  </Button>
                )
              }
            >
              <DescriptionsItem label="Cliente" value={selectedOrder.customer_name || "N/A"} />
              <DescriptionsItem label="Prioridad" value={<Tag>{selectedOrder.priority}</Tag>} />
              <DescriptionsItem label="Estado" value={<Tag color="blue">{selectedOrder.status}</Tag>} />

              <div style={{ marginTop: 24, marginBottom: 12, fontWeight: 600 }}>Líneas del Pedido</div>
              <Table
                dataSource={selectedOrder.lines}
                size="small"
                pagination={false}
                columns={[
                  { title: "SKU", dataIndex: ["product", "sku"], key: "sku" },
                  { title: "Producto", dataIndex: ["product", "name"], key: "name" },
                  { title: "Requerido", dataIndex: "requested_quantity", key: "req" },
                  { title: "Recolectado", dataIndex: "picked_quantity", key: "picked" },
                  {
                    title: "Estado",
                    dataIndex: "status",
                    key: "status",
                    render: s => <Tag color={s === "PICKED" ? "success" : "default"}>{s}</Tag>
                  }
                ]}
                rowKey="id"
              />
            </Card>
          ) : (
            <Card className="glass-panel" style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <div style={{ textAlign: "center", padding: "40px 0", color: "#64748b" }}>
                <InboxOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>Selecciona un pedido para ver el desglose y asignar operarios</div>
              </div>
            </Card>
          )}
        </Col>
      </Row>

      {/* Operator Tasks List */}
      <Card title="Mis Tareas de Picking Activas (Operario)" className="glass-panel">
        <Table
          dataSource={operatorTasks}
          locale={{ emptyText: "No tienes tareas de picking pendientes en este momento" }}
          columns={[
            { title: "SKU", dataIndex: ["product", "sku"], key: "sku" },
            { title: "Producto", dataIndex: ["product", "name"], key: "name" },
            {
              title: "Ubicación Origen",
              dataIndex: ["from_location", "code"],
              key: "from_loc",
              render: text => <Text style={{ color: "#00d4ff", fontWeight: 600 }}><EnvironmentOutlined /> {text}</Text>
            },
            { title: "Cantidad a Recolectar", dataIndex: "quantity_to_pick", key: "qty" },
            {
              title: "Acción",
              key: "action",
              render: (_, record) => (
                <Button size="small" type="primary" onClick={() => handleOpenPickTask(record)}>
                  Confirmar Recolección
                </Button>
              )
            }
          ]}
          rowKey="id"
        />
      </Card>

      {/* Create Order Modal */}
      <Modal title="Crear Pedido de Salida" open={isNewModalOpen} onCancel={() => setIsNewModalOpen(false)} onOk={() => newOrderForm.submit()} width={720}>
        <Form form={newOrderForm} layout="vertical" onFinish={handleCreateOrder}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="warehouse_id" label="Bodega de Origen" rules={[{ required: true }]}>
                <Select>
                  {warehouses.map(w => (
                    <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="customer_name" label="Nombre Cliente / Destinatario" rules={[{ required: true }]}>
                <Input placeholder="Ej. Tienda Centro Santiago" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="priority" label="Prioridad" initialValue="MEDIUM">
                <Select>
                  <Select.Option value="LOW">Baja</Select.Option>
                  <Select.Option value="MEDIUM">Media</Select.Option>
                  <Select.Option value="HIGH">Alta</Select.Option>
                  <Select.Option value="URGENT">Urgente</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="notes" label="Notas de Preparación">
                <Input />
              </Form.Item>
            </Col>
          </Row>

          <Card title="Agregar Productos a Pedido" size="small" style={{ marginTop: 16 }}>
            <Form layout="inline" onFinish={handleAddItemToNewOrder}>
              <Form.Item name="product_id" rules={[{ required: true }]} style={{ width: "60%" }}>
                <Select placeholder="Seleccionar SKU" showSearch optionFilterProp="children">
                  {products.map(p => (
                    <Select.Option key={p.id} value={p.id}>{p.name} (SKU: {p.sku})</Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="requested_quantity" rules={[{ required: true }]} style={{ width: "25%" }}>
                <Input type="number" placeholder="Cant." />
              </Form.Item>
              <Form.Item style={{ width: "10%" }}>
                <Button type="primary" htmlType="submit" icon={<PlusOutlined />} />
              </Form.Item>
            </Form>
            <List
              style={{ marginTop: 12, maxHeight: 150, overflowY: "auto" }}
              size="small"
              dataSource={newOrderItems}
              renderItem={item => (
                <List.Item>
                  <Text>{item.name} (SKU: {item.sku})</Text>
                  <Tag color="blue">{item.requested_quantity} unidades</Tag>
                </List.Item>
              )}
            />
          </Card>
        </Form>
      </Modal>

      {/* Assign Picking Modal */}
      <Modal title="Asignar Operario de Picking" open={isAssignModalOpen} onCancel={() => setIsAssignModalOpen(false)} onOk={() => assignForm.submit()}>
        <Form form={assignForm} layout="vertical" onFinish={handleAssignOrder}>
          <Form.Item name="operator_id" label="Operador Responsable" rules={[{ required: true }]}>
            <Select>
              {operators.map(op => (
                <Select.Option key={op.id} value={op.id}>{op.full_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="strategy" label="Algoritmo de Ruteo / Ubicación" initialValue="FIFO">
            <Select>
              <Select.Option value="FIFO">FIFO (First In, First Out — Por fecha de ingreso)</Select.Option>
              <Select.Option value="FEFO">FEFO (First Expiry, First Out — Por vencimiento de lote)</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Pick Task Execution Modal */}
      <Modal title="Confirmar Recolección Física" open={isPickModalOpen} onCancel={() => setIsPickModalOpen(false)} onOk={() => pickForm.submit()}>
        <Form form={pickForm} layout="vertical" onFinish={handleExecutePick}>
          <DescriptionsItem label="Producto" value={activeTask?.product?.name} />
          <DescriptionsItem label="Ubicación Rack" value={activeTask?.from_location?.code} />
          <DescriptionsItem label="Cantidad Solicitada" value={activeTask?.quantity_to_pick} />
          
          <Form.Item name="picked_quantity" label="Cantidad Recolectada" rules={[{ required: true }]} style={{ marginTop: 16 }}>
            <Input type="number" step="0.01" />
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

export default Orders;
