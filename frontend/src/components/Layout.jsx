import React, { useState } from "react";
import { Layout as AntLayout, Menu, Button, Avatar, Dropdown, Space, Tag } from "antd";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  HomeOutlined,
  BarcodeOutlined,
  DatabaseOutlined,
  DownloadOutlined,
  InboxOutlined,
  UploadOutlined,
  AlertOutlined,
  UserOutlined,
  LogoutOutlined,
  KeyOutlined
} from "@ant-design/icons";
import useAuthStore from "../stores/authStore";

const { Header, Sider, Content } = AntLayout;

const Layout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isUserAdmin = user?.roles?.some(r => r.name.toUpperCase() === "ADMIN") || user?.is_superuser;

  const menuItems = [
    {
      key: "/",
      icon: <DashboardOutlined />,
      label: <Link to="/">Dashboard</Link>,
    },
    {
      key: "/warehouses",
      icon: <HomeOutlined />,
      label: <Link to="/warehouses">Bodegas y Ubicaciones</Link>,
    },
    {
      key: "/products",
      icon: <BarcodeOutlined />,
      label: <Link to="/products">Productos</Link>,
    },
    {
      key: "/inventory",
      icon: <DatabaseOutlined />,
      label: <Link to="/inventory">Inventario</Link>,
    },
    {
      key: "/reception",
      icon: <DownloadOutlined />,
      label: <Link to="/reception">Recepción</Link>,
    },
    {
      key: "/orders",
      icon: <InboxOutlined />,
      label: <Link to="/orders">Picking y Pedidos</Link>,
    },
    {
      key: "/dispatch",
      icon: <UploadOutlined />,
      label: <Link to="/dispatch">Despachos</Link>,
    },
    {
      key: "/alerts",
      icon: <AlertOutlined />,
      label: <Link to="/alerts">Alertas</Link>,
    },
  ];

  // Admin-only menu items
  if (isUserAdmin) {
    menuItems.push({
      key: "/users",
      icon: <UserOutlined />,
      label: <Link to="/users">Usuarios</Link>,
    });
  }

  const userMenu = {
    items: [
      {
        key: "profile",
        icon: <KeyOutlined />,
        label: "Cambiar Contraseña",
      },
      {
        type: "divider",
      },
      {
        key: "logout",
        icon: <LogoutOutlined />,
        label: "Cerrar Sesión",
        onClick: handleLogout,
      },
    ],
  };

  return (
    <AntLayout style={{ minHeight: "100vh" }}>
      <Sider trigger={null} collapsible collapsed={collapsed} width={260}>
        <div style={{
          height: 64,
          margin: 16,
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "flex-start",
          gap: 12,
          paddingLeft: collapsed ? 0 : 8
        }}>
          <div style={{
            width: 36,
            height: 36,
            borderRadius: 8,
            background: "linear-gradient(135deg, #1890ff, #00d4ff)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: "bold",
            fontSize: 18,
            color: "#fff"
          }}>
            W
          </div>
          {!collapsed && (
            <span style={{ fontSize: 18, fontWeight: 800, color: "#f8fafc", letterSpacing: 1 }}>
              SmartWMS <span style={{ color: "#00d4ff" }}>AI</span>
            </span>
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
        />
      </Sider>
      <AntLayout>
        <Header style={{ padding: "0 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: "16px", width: 64, height: 64, color: "#94a3b8" }}
          />
          <Space size="middle">
            <Tag color="cyan" style={{ border: "none", padding: "4px 8px", fontSize: 13 }}>
              {user?.roles?.[0]?.name || "Viewer"}
            </Tag>
            <Dropdown menu={userMenu} placement="bottomRight" arrow>
              <Space style={{ cursor: "pointer" }}>
                <Avatar style={{ backgroundColor: "#1890ff" }} icon={<UserOutlined />} />
                <span style={{ color: "#e2e8f0", fontWeight: 500 }}>{user?.full_name}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ margin: "24px 16px", padding: 24, minHeight: 280, overflowY: "auto" }}>
          {children}
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

export default Layout;
