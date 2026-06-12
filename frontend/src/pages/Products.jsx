import React, { useEffect, useState } from "react";
import { Table, Card, Button, Form, Input, Modal, Select, Row, Col, Space, Typography, Tag, message } from "antd";
import { PlusOutlined, BarcodeOutlined, EditOutlined } from "@ant-design/icons";
import client from "../api/client";

const { Title, Text } = Typography;

const Products = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isProdModalOpen, setIsProdModalOpen] = useState(false);
  const [isCatModalOpen, setIsCatModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);

  const [prodForm] = Form.useForm();
  const [catForm] = Form.useForm();

  const loadProducts = async () => {
    setLoading(true);
    try {
      const res = await client.get("/products/");
      setProducts(res.data);
    } catch (err) {
      message.error("Error al cargar catálogo de productos");
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const res = await client.get("/products/categories");
      setCategories(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadProducts();
    loadCategories();
  }, []);

  const handleCreateProduct = async (values) => {
    try {
      if (editingProduct) {
        await client.put(`/products/${editingProduct.id}`, values);
        message.success("Producto actualizado correctamente");
      } else {
        await client.post("/products/", values);
        message.success("Producto creado correctamente");
      }
      setIsProdModalOpen(false);
      setEditingProduct(null);
      prodForm.resetFields();
      loadProducts();
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al registrar producto");
    }
  };

  const handleCreateCategory = async (values) => {
    try {
      await client.post("/products/categories", values);
      message.success("Categoría creada correctamente");
      setIsCatModalOpen(false);
      catForm.resetFields();
      loadCategories();
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al crear categoría");
    }
  };

  const startEdit = (product) => {
    setEditingProduct(product);
    prodForm.setFieldsValue({
      ...product,
      category_id: product.category?.id
    });
    setIsProdModalOpen(true);
  };

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <Title level={3} style={{ margin: 0, color: "#f8fafc" }}>Catálogo de Productos (SKU)</Title>
          <Text style={{ color: "#94a3b8" }}>Administra los artículos, códigos de barras, y umbrales mínimos/máximos</Text>
        </div>
        <Space>
          <Button icon={<PlusOutlined />} onClick={() => setIsCatModalOpen(true)}>
            Nueva Categoría
          </Button>
          <Button type="primary" icon={<BarcodeOutlined />} onClick={() => { setEditingProduct(null); prodForm.resetFields(); setIsProdModalOpen(true); }}>
            Nuevo Producto
          </Button>
        </Space>
      </div>

      <Card className="glass-panel" bodyStyle={{ padding: 0 }}>
        <Table
          loading={loading}
          dataSource={products}
          columns={[
            {
              title: "SKU",
              dataIndex: "sku",
              key: "sku",
              render: sku => <Text style={{ fontWeight: 600, color: "#00d4ff" }}>{sku}</Text>
            },
            { title: "Nombre del Producto", dataIndex: "name", key: "name" },
            {
              title: "Categoría",
              dataIndex: ["category", "name"],
              key: "category",
              render: text => text ? <Tag color="blue">{text}</Tag> : <Tag color="default">Sin Categoría</Tag>
            },
            { title: "U. Medida", dataIndex: "unit_of_measure", key: "unit_of_measure" },
            {
              title: "Dimensiones (Peso/Vol)",
              key: "dimensions",
              render: (_, record) => `${record.weight} kg / ${record.volume} m3`
            },
            {
              title: "Umbral Stock Min/Max",
              key: "min_max",
              render: (_, record) => `Mín: ${record.min_stock} / Máx: ${record.max_stock}`
            },
            {
              title: "Estado",
              dataIndex: "is_active",
              key: "is_active",
              render: active => active ? <Tag color="success">Activo</Tag> : <Tag color="error">Inactivo</Tag>
            },
            {
              title: "Acciones",
              key: "actions",
              render: (_, record) => (
                <Button size="small" icon={<EditOutlined />} onClick={() => startEdit(record)}>
                  Editar
                </Button>
              )
            }
          ]}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Product Create/Edit Modal */}
      <Modal
        title={editingProduct ? "Editar Producto" : "Crear Nuevo Producto"}
        open={isProdModalOpen}
        onCancel={() => { setIsProdModalOpen(false); setEditingProduct(null); }}
        onOk={() => prodForm.submit()}
        width={720}
      >
        <Form form={prodForm} layout="vertical" onFinish={handleCreateProduct}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="sku" label="Código SKU" rules={[{ required: true }]}>
                <Input disabled={!!editingProduct} placeholder="Ej. PROD-LAP01" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="name" label="Nombre Comercial" rules={[{ required: true }]}>
                <Input placeholder="Ej. Laptop Pro 15.6" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="Descripción del Producto">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="category_id" label="Categoría">
                <Select placeholder="Seleccionar Categoría">
                  {categories.map(c => (
                    <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="barcode" label="Código de Barras / EAN">
                <Input placeholder="Ej. 742839210923" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="unit_of_measure" label="Unidad de Medida" initialValue="UNIDAD">
                <Select>
                  <Select.Option value="UNIDAD">Unidad</Select.Option>
                  <Select.Option value="KG">Kilogramos (kg)</Select.Option>
                  <Select.Option value="LITROS">Litros (L)</Select.Option>
                  <Select.Option value="CAJA">Caja</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="weight" label="Peso Unitario (kg)" initialValue={0.0}>
                <Input type="number" step="0.01" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="volume" label="Volumen Unitario (m3)" initialValue={0.0}>
                <Input type="number" step="0.0001" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="min_stock" label="Stock Mínimo (Alerta)" initialValue={0.0}>
                <Input type="number" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="max_stock" label="Stock Máximo" initialValue={0.0}>
                <Input type="number" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="reorder_point" label="Punto de Reorden" initialValue={0.0}>
                <Input type="number" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Category Modal */}
      <Modal title="Crear Nueva Categoría" open={isCatModalOpen} onCancel={() => setIsCatModalOpen(false)} onOk={() => catForm.submit()}>
        <Form form={catForm} layout="vertical" onFinish={handleCreateCategory}>
          <Form.Item name="name" label="Nombre de Categoría" rules={[{ required: true }]}>
            <Input placeholder="Ej. Alimentos Perecibles" />
          </Form.Item>
          <Form.Item name="description" label="Descripción">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Products;
