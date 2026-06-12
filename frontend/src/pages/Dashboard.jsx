import React, { useEffect, useState } from "react";
import { Row, Col, Card, Statistic, List, Alert, Timeline, Input, Button, Avatar, Space, Typography, Tag, Select, Spin } from "antd";
import {
  PieChartOutlined,
  CheckCircleOutlined,
  DashboardOutlined,
  WarningOutlined,
  SyncOutlined,
  ArrowUpOutlined,
  SendOutlined,
  RobotOutlined,
  InboxOutlined
} from "@ant-design/icons";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from "recharts";
import client from "../api/client";

const { Title, Text } = Typography;

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [chatQuery, setChatQuery] = useState("");
  const [chatLog, setChatLog] = useState([
    { sender: "ai", text: "¡Hola! Soy tu Asistente Logístico con IA. ¿En qué puedo ayudarte hoy?" }
  ]);
  const [sendingChat, setSendingChat] = useState(false);
  const [warehouseId, setWarehouseId] = useState("");
  const [warehouses, setWarehouses] = useState([]);

  useEffect(() => {
    const fetchInitial = async () => {
      try {
        const whRes = await client.get("/warehouses/");
        setWarehouses(whRes.data);
        if (whRes.data.length > 0) {
          setWarehouseId(whRes.data[0].id);
        }
      } catch (err) {
        console.error("Error loading warehouses", err);
      }
    };
    fetchInitial();
  }, []);

  useEffect(() => {
    if (!warehouseId) return;
    const fetchDashboard = async () => {
      setLoading(true);
      try {
        const res = await client.get(`/dashboard/summary/${warehouseId}`);
        setData(res.data);
      } catch (err) {
        console.error("Error loading dashboard data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, [warehouseId]);

  const handleSendChat = async () => {
    if (!chatQuery.trim()) return;
    const userMsg = chatQuery;
    setChatLog(prev => [...prev, { sender: "user", text: userMsg }]);
    setChatQuery("");
    setSendingChat(true);

    try {
      const res = await client.post("/dashboard/nlp-assistant", {
        warehouse_id: warehouseId,
        query_text: userMsg
      });
      setChatLog(prev => [...prev, { sender: "ai", text: res.data.response }]);
    } catch (err) {
      setChatLog(prev => [...prev, { sender: "ai", text: "Disculpa, hubo un problema al conectar con el motor de IA." }]);
    } finally {
      setSendingChat(false);
    }
  };

  const chartData = [
    { name: "Semana 1", Entradas: 400, Salidas: 240 },
    { name: "Semana 2", Entradas: 300, Salidas: 139 },
    { name: "Semana 3", Entradas: 200, Salidas: 980 },
    { name: "Semana 4", Entradas: 278, Salidas: 390 },
    { name: "Semana 5", Entradas: 189, Salidas: 480 },
  ];

  if (loading && !data) {
    return (
      <div style={{ textAlign: "center", padding: "100px 0" }}>
        <Spin size="large" tip="Cargando métricas en tiempo real..." />
      </div>
    );
  }

  const kpis = data?.kpis || {
    fill_rate: 0,
    otif: 0,
    inventory_accuracy: 0,
    inventory_rotation: 0,
    productivity_picking: 0,
    stockouts_count: 0
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <Title level={3} style={{ margin: 0, color: "#f8fafc" }}>Dashboard Operacional</Title>
          <Text style={{ color: "#94a3b8" }}>Supervisión inteligente y métricas logísticas clave</Text>
        </div>
        <Select
          style={{ width: 220 }}
          placeholder="Seleccionar Bodega"
          value={warehouseId}
          onChange={setWarehouseId}
        >
          {warehouses.map(w => (
            <Select.Option key={w.id} value={w.id}>{w.name}</Select.Option>
          ))}
        </Select>
      </div>

      {/* KPI Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card className="glass-panel" bordered={false}>
            <Statistic
              title={<span style={{ color: "#94a3b8" }}>Fill Rate Pedidos</span>}
              value={kpis.fill_rate}
              precision={1}
              valueStyle={{ color: "#10b981", fontWeight: 700 }}
              prefix={<CheckCircleOutlined />}
              suffix="%"
            />
            <div style={{ marginTop: 8 }}><Tag color="success">Objetivo: 98%</Tag></div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="glass-panel" bordered={false}>
            <Statistic
              title={<span style={{ color: "#94a3b8" }}>OTIF (Entregas Completas y a Tiempo)</span>}
              value={kpis.otif}
              precision={1}
              valueStyle={{ color: "#00d4ff", fontWeight: 700 }}
              prefix={<DashboardOutlined />}
              suffix="%"
            />
            <div style={{ marginTop: 8 }}><Tag color="processing">Objetivo: 95%</Tag></div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="glass-panel" bordered={false}>
            <Statistic
              title={<span style={{ color: "#94a3b8" }}>Exactitud de Inventario (IRA)</span>}
              value={kpis.inventory_accuracy}
              precision={1}
              valueStyle={{ color: "#f59e0b", fontWeight: 700 }}
              prefix={<SyncOutlined spin={loading} />}
              suffix="%"
            />
            <div style={{ marginTop: 8 }}><Tag color="warning">Objetivo: 99.5%</Tag></div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="glass-panel" bordered={false}>
            <Statistic
              title={<span style={{ color: "#94a3b8" }}>Quiebres de Stock</span>}
              value={kpis.stockouts_count}
              valueStyle={{ color: kpis.stockouts_count > 0 ? "#ef4444" : "#10b981", fontWeight: 700 }}
              prefix={<WarningOutlined />}
            />
            <div style={{ marginTop: 8 }}>
              <Tag color={kpis.stockouts_count > 0 ? "error" : "success"}>
                {kpis.stockouts_count > 0 ? "Requiere Atención" : "Sin Quiebres"}
              </Tag>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* Main Chart */}
        <Col xs={24} lg={16}>
          <Card title="Productividad y Flujo de Inventario (Semanas)" className="glass-panel" style={{ height: "100%" }}>
            <div style={{ width: "100%", height: 300 }}>
              <ResponsiveContainer>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorEntradas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#1890ff" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#1890ff" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorSalidas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#00d4ff" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} />
                  <Legend />
                  <Area type="monotone" dataKey="Entradas" stroke="#1890ff" fillOpacity={1} fill="url(#colorEntradas)" />
                  <Area type="monotone" dataKey="Salidas" stroke="#00d4ff" fillOpacity={1} fill="url(#colorSalidas)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>

        {/* AI Assistant Console */}
        <Col xs={24} lg={8}>
          <Card
            title={
              <Space>
                <RobotOutlined style={{ color: "#00d4ff" }} />
                <span>Asistente Logístico IA</span>
              </Space>
            }
            className="glass-panel"
            style={{ height: "100%", display: "flex", flexDirection: "column" }}
            bodyStyle={{ display: "flex", flexDirection: "column", flexGrow: 1, padding: 12 }}
          >
            <div style={{
              flexGrow: 1,
              height: 200,
              overflowY: "auto",
              background: "rgba(0,0,0,0.2)",
              borderRadius: 8,
              padding: 12,
              marginBottom: 12,
              border: "1px solid rgba(255,255,255,0.05)"
            }}>
              {chatLog.map((log, idx) => (
                <div key={idx} style={{
                  marginBottom: 12,
                  display: "flex",
                  justifyContent: log.sender === "user" ? "flex-end" : "flex-start"
                }}>
                  <Space align="start" size={8} style={{ maxWidth: "85%" }}>
                    {log.sender === "ai" && <Avatar size="small" icon={<RobotOutlined />} style={{ backgroundColor: "#1e293b", color: "#00d4ff" }} />}
                    <div style={{
                      backgroundColor: log.sender === "user" ? "#1890ff" : "rgba(255, 255, 255, 0.05)",
                      padding: "8px 12px",
                      borderRadius: 12,
                      fontSize: 13,
                      color: "#f8fafc",
                      whiteSpace: "pre-line"
                    }}>
                      {log.text}
                    </div>
                  </Space>
                </div>
              ))}
              {sendingChat && <Spin size="small" style={{ margin: "10px 0 0 25px" }} />}
            </div>
            <Space.Compact style={{ width: "100%" }}>
              <Input
                placeholder="Pregúntale a la IA (ej. ¿Qué SKU tienen riesgo?)"
                value={chatQuery}
                onChange={e => setChatQuery(e.target.value)}
                onPressEnter={handleSendChat}
                style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "#fff" }}
              />
              <Button type="primary" icon={<SendOutlined />} onClick={handleSendChat} loading={sendingChat} />
            </Space.Compact>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* Recent Alerts */}
        <Col xs={24} md={12}>
          <Card title="Alertas de Inventario Críticas" className="glass-panel">
            <List
              dataSource={data?.recent_alerts || []}
              renderItem={alert => (
                <List.Item style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                  <Space align="start">
                    <WarningOutlined style={{ color: alert.severity === "CRITICAL" ? "#ef4444" : "#f59e0b", fontSize: 16, marginTop: 4 }} />
                    <div>
                      <div style={{ fontWeight: 600, color: "#f8fafc" }}>{alert.title}</div>
                      <div style={{ fontSize: 12, color: "#94a3b8" }}>{alert.message}</div>
                    </div>
                  </Space>
                  <Tag color="magenta">{alert.type}</Tag>
                </List.Item>
              )}
              locale={{ emptyText: <Text style={{ color: "#64748b" }}>Sin alertas pendientes</Text> }}
            />
          </Card>
        </Col>

        {/* Recent Movements */}
        <Col xs={24} md={12}>
          <Card title="Movimientos Recientes de Stock" className="glass-panel">
            <Timeline
              style={{ marginTop: 16 }}
              items={(data?.recent_movements || []).map(m => ({
                color: m.type === "ENTRY" ? "green" : m.type === "EXIT" ? "red" : "blue",
                children: (
                  <div>
                    <span style={{ fontWeight: 600, color: "#f8fafc" }}>
                      {m.type === "ENTRY" ? "Ingreso" : m.type === "EXIT" ? "Salida" : "Transferencia"} de {m.qty} unidades
                    </span>
                    <p style={{ margin: 0, fontSize: 12, color: "#94a3b8" }}>
                      {m.product_name} (SKU: {m.sku}) — {new Date(m.date).toLocaleTimeString()}
                    </p>
                  </div>
                )
              }))}
            />
            {(!data?.recent_movements || data.recent_movements.length === 0) && (
              <div style={{ textAlign: "center", padding: "24px 0", color: "#64748b" }}>
                Sin movimientos recientes
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
