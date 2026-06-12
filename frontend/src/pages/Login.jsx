import React, { useEffect } from "react";
import { Form, Input, Button, Card, Alert, Typography } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import useAuthStore from "../stores/authStore";

const { Title, Text } = Typography;

const Login = () => {
  const { login, isAuthenticated, loading, error, clearError } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    clearError();
    if (isAuthenticated) {
      navigate("/");
    }
  }, [isAuthenticated, navigate, clearError]);

  const onFinish = async (values) => {
    const success = await login(values.email, values.password);
    if (success) {
      navigate("/");
    }
  };

  return (
    <div style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      minHeight: "100vh",
      background: "radial-gradient(circle at center, #0f172a 0%, #020617 100%)"
    }}>
      <Card
        className="glass-panel"
        style={{
          width: 420,
          border: "1px solid rgba(255, 255, 255, 0.08)",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.5)"
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: "linear-gradient(135deg, #1890ff, #00d4ff)",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: "bold",
            fontSize: 24,
            color: "#fff",
            marginBottom: 16
          }}>
            W
          </div>
          <Title level={2} style={{ margin: 0, color: "#f8fafc" }}>
            SmartWMS <span style={{ color: "#00d4ff" }}>AI</span>
          </Title>
          <Text style={{ color: "#94a3b8" }}>Inicia sesión para gestionar tu inventario</Text>
        </div>

        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{ marginBottom: 24, borderRadius: 8 }}
            closable
            onClose={clearError}
          />
        )}

        <Form
          name="login_form"
          initialValues={{ remember: true }}
          onFinish={onFinish}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: "Por favor ingresa tu correo" },
              { type: "email", message: "Ingresa un correo válido" }
            ]}
          >
            <Input
              prefix={<UserOutlined style={{ color: "#64748b" }} />}
              placeholder="correo@smartwms.com"
              style={{ background: "rgba(0,0,0,0.2)", border: "1px solid rgba(255,255,255,0.08)", color: "#fff" }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: "Por favor ingresa tu contraseña" }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: "#64748b" }} />}
              placeholder="Contraseña"
              style={{ background: "rgba(0,0,0,0.2)", border: "1px solid rgba(255,255,255,0.08)", color: "#fff" }}
            />
          </Form.Item>

          <Form.Item style={{ marginTop: 32 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ height: 45, fontSize: 16, fontWeight: 600 }}
            >
              Iniciar Sesión
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: "center", marginTop: 16 }}>
          <Text style={{ color: "#475569", fontSize: 12 }}>
            Demo: admin@smartwms.com / admin123
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default Login;
