import React, { useEffect, useState } from "react";
import { Table, Card, Button, Form, Input, Modal, Select, Tag, message } from "antd";
import { PlusOutlined, UserOutlined, UserAddOutlined } from "@ant-design/icons";
import client from "../api/client";

const Users = () => {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [form] = Form.useForm();

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await client.get("/users/");
      setUsers(res.data);
    } catch (err) {
      message.error("Error al cargar usuarios");
    } finally {
      setLoading(false);
    }
  };

  const loadRoles = async () => {
    try {
      const res = await client.get("/users/roles");
      setRoles(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadUsers();
    loadRoles();
  }, []);

  const handleCreateUser = async (values) => {
    try {
      // 1. Register user
      const regRes = await client.post("/auth/register", {
        email: values.email,
        password: values.password,
        full_name: values.full_name,
        is_active: true
      });
      
      const newUserId = regRes.data.id;
      
      // 2. Assign selected role by updating role lists
      await client.put(`/users/${newUserId}`, {
        role_ids: [values.role_id]
      });
      
      message.success("Usuario registrado y asignado a rol");
      setIsModalOpen(false);
      form.resetFields();
      loadUsers();
    } catch (err) {
      message.error(err.response?.data?.detail || "Error al registrar usuario");
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 style={{ margin: 0, color: "#f8fafc", fontSize: 20 }}>Gestión de Operadores y Usuarios</h3>
          <span style={{ color: "#94a3b8" }}>Controla quién accede y asigna roles operacionales</span>
        </div>
        <Button type="primary" icon={<UserAddOutlined />} onClick={() => setIsModalOpen(true)}>
          Nuevo Colaborador
        </Button>
      </div>

      <Card className="glass-panel" bodyStyle={{ padding: 0 }}>
        <Table
          loading={loading}
          dataSource={users}
          columns={[
            { title: "Nombre Completo", dataIndex: "full_name", key: "name" },
            { title: "Correo Electrónico", dataIndex: "email", key: "email" },
            {
              title: "Roles Asignados",
              dataIndex: "roles",
              key: "roles",
              render: userRoles => (
                <>
                  {userRoles.map(r => (
                    <Tag color="cyan" key={r.id}>{r.name}</Tag>
                  ))}
                  {userRoles.length === 0 && <Tag>Sin Rol</Tag>}
                </>
              )
            },
            {
              title: "Estado",
              dataIndex: "is_active",
              key: "active",
              render: active => active ? <Tag color="success">Activo</Tag> : <Tag color="error">Inactivo</Tag>
            }
          ]}
          rowKey="id"
        />
      </Card>

      <Modal title="Registrar Colaborador" open={isModalOpen} onCancel={() => setIsModalOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={handleCreateUser}>
          <Form.Item name="full_name" label="Nombre Completo" rules={[{ required: true }]}>
            <Input placeholder="Ej. Juan Pérez" />
          </Form.Item>
          <Form.Item name="email" label="Correo Corporativo" rules={[{ required: true, type: "email" }]}>
            <Input placeholder="juan@empresa.com" />
          </Form.Item>
          <Form.Item name="password" label="Contraseña Temporal" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="role_id" label="Rol WMS" rules={[{ required: true }]}>
            <Select placeholder="Seleccionar Rol">
              {roles.map(r => (
                <Select.Option key={r.id} value={r.id}>{r.name} — {r.description}</Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Users;
