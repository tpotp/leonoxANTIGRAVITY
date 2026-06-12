import React, { useEffect, useState } from "react";
import { Table, Card, Button, Space, Typography, Tag, message } from "antd";
import { AlertOutlined, CheckOutlined, SyncOutlined } from "@ant-design/icons";
import client from "../api/client";

const { Title, Text } = Typography;

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [warehouseId, setWarehouseId] = useState("");

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const res = await client.get("/alerts/");
      setAlerts(res.data);
    } catch (err) {
      message.error("Error al cargar alertas");
    } finally {
      setLoading(false);
    }
  };

  const loadWarehouse = async () => {
    try {
      const res = await client.get("/warehouses/");
      if (res.data.length > 0) {
        setWarehouseId(res.data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadAlerts();
    loadWarehouse();
  }, []);

  const handleResolve = async (id) => {
    try {
      await client.put(`/alerts/${id}/resolve`);
      message.success("Alerta marcada como resuelta");
      loadAlerts();
    } catch (err) {
      message.error("Error al resolver la alerta");
    }
  };

  const handleManualScan = async () => {
    if (!warehouseId) return;
    setLoading(true);
    try {
      await client.post(`/alerts/check/${warehouseId}`);
      message.success("Escaneo de inventario completado. Alertas actualizadas.");
      loadAlerts();
    } catch (err) {
      message.error("Error al ejecutar escaneo");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <Title level={3} style={{ margin: 0, color: "#f8fafc" }}>Gestión de Alertas</Title>
          <Text style={{ color: "#94a3b8" }}>Supervisa quiebres de stock, sobrestock, lotes próximos a vencer o inmovilizados</Text>
        </div>
        <Space>
          <Button icon={<SyncOutlined />} onClick={loadAlerts}>
            Refrescar
          </Button>
          <Button type="primary" danger icon={<AlertOutlined />} onClick={handleManualScan} loading={loading}>
            Escanear Inventario
          </Button>
        </Space>
      </div>

      <Card className="glass-panel" bodyStyle={{ padding: 0 }}>
        <Table
          loading={loading}
          dataSource={alerts}
          columns={[
            {
              title: "Severidad",
              dataIndex: "severity",
              key: "severity",
              render: sev => {
                const colors = { CRITICAL: "red", WARNING: "orange", INFO: "blue" };
                return <Tag color={colors[sev] || "blue"}>{sev}</Tag>;
              }
            },
            { title: "Título", dataIndex: "title", key: "title" },
            { title: "Descripción", dataIndex: "message", key: "message" },
            {
              title: "Tipo",
              dataIndex: "alert_type",
              key: "type",
              render: text => <Tag color="geekblue">{text}</Tag>
            },
            {
              title: "Fecha",
              dataIndex: "created_at",
              key: "date",
              render: date => new Date(date).toLocaleString()
            },
            {
              title: "Resolución",
              key: "resolution",
              render: (_, record) => {
                if (record.is_resolved) {
                  return <Tag color="success">Resuelta</Tag>;
                }
                return (
                  <Button size="small" type="primary" ghost icon={<CheckOutlined />} onClick={() => handleResolve(record.id)}>
                    Resolver
                  </Button>
                );
              }
            }
          ]}
          rowKey="id"
        />
      </Card>
    </div>
  );
};

export default Alerts;
