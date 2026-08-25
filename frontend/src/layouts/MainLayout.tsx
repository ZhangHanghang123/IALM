/**
 * IALM 主布局（二级菜单，仿 ALMD 风格）
 */
import { useState, useEffect } from 'react'
import { Layout, Menu, Avatar, Dropdown, Space, Typography } from 'antd'
import {
  DashboardOutlined, DatabaseOutlined, LineChartOutlined,
  ExperimentOutlined, FundOutlined, AlertOutlined,
  FileSearchOutlined, HistoryOutlined, AppstoreOutlined,
  UserOutlined, LogoutOutlined, ClusterOutlined,
  DollarOutlined, BankOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const { Header, Sider, Content, Footer } = Layout
const { Text } = Typography

const menuItems = [
  {
    key: '/group-home',
    label: '首页概览',
    icon: <DashboardOutlined />,
    children: [
      { key: '/dashboard', label: '系统仪表盘' },
      { key: '/regulatory-overview', label: '监管全景监控' },
    ],
  },
  {
    key: '/group-data',
    label: '基础数据',
    icon: <DatabaseOutlined />,
    children: [
      { key: '/companies', label: '保险公司' },
      { key: '/assets', icon: <DollarOutlined />, label: '资产端管理' },
      { key: '/liabilities', icon: <BankOutlined />, label: '负债端管理' },
      { key: '/market-data', label: '市场数据' },
    ],
  },
  {
    key: '/group-rule5',
    label: '5号规则分析',
    icon: <LineChartOutlined />,
    children: [
      { key: '/match', label: '综合分析' },
      { key: '/duration-match', label: '期限匹配率' },
      { key: '/cost-yield', label: '成本收益比' },
      { key: '/cashflow-payback', label: '现金流回正期' },
    ],
  },
  {
    key: '/group-cashflow',
    label: '现金流预测',
    icon: <ClusterOutlined />,
    children: [
      { key: '/cashflow-forecast', label: '现金流预测' },
      { key: '/monte-carlo', label: '蒙特卡洛模拟' },
    ],
  },
  {
    key: '/group-stress',
    label: '压力测试',
    icon: <ExperimentOutlined />,
    children: [
      { key: '/stress-scenarios', label: '监管情景' },
      { key: '/stress-results', label: '测试结果' },
      { key: '/stress-run', label: '运行模拟' },
    ],
  },
  {
    key: '/group-portfolio',
    label: '投资组合',
    icon: <FundOutlined />,
    children: [
      { key: '/markowitz', label: 'Markowitz 配置' },
      { key: '/black-litterman', label: 'Black-Litterman' },
      { key: '/allocations', label: '资产配置' },
      { key: '/attributions', label: 'Brinson 业绩归因' },
    ],
  },
  {
    key: '/group-risk',
    label: '风险与监管',
    icon: <AlertOutlined />,
    children: [
      { key: '/risk-preferences', label: '风险偏好' },
      { key: '/risk-indicators', label: '风险指标' },
      { key: '/risk-events', label: '风险事件' },
      { key: '/regulatory-reports', label: '监管报表' },
    ],
  },
  {
    key: '/group-knowledge',
    label: '算法引擎',
    icon: <AppstoreOutlined />,
    children: [
      { key: '/algorithms', label: '14 项算法' },
      { key: '/models', label: '模型定义' },
      { key: '/model-versions', label: '模型版本' },
      { key: '/history', icon: <HistoryOutlined />, label: '分析历史' },
    ],
  },
]

export default function MainLayout() {
  const nav = useNavigate()
  const loc = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const [openKeys, setOpenKeys] = useState<string[]>(['/group-home'])
  const [user, setUser] = useState<any>({})

  useEffect(() => {
    const stored = localStorage.getItem('ialm_user')
    if (stored) {
      try { setUser(JSON.parse(stored)) } catch {}
    }
  }, [])

  // 自动展开当前路由所在的 group
  useEffect(() => {
    for (const item of menuItems) {
      if (item.children?.some((c: any) => loc.pathname.startsWith(c.key))) {
        if (!openKeys.includes(item.key)) {
          setOpenKeys(prev => [...prev, item.key])
        }
        break
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loc.pathname])

  const selectedKey =
    menuItems
      .flatMap(m => m.children || [m])
      .find(c => loc.pathname.startsWith(c.key))?.key || '/dashboard'

  const currentLabel =
    menuItems
      .flatMap(m => m.children || [m])
      .find(c => c.key === selectedKey)?.label || 'IALM'

  const userMenu = {
    items: [
      { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === 'logout') {
        localStorage.removeItem('ialm_token')
        localStorage.removeItem('ialm_user')
        nav('/login')
      }
    },
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        width={220}
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{ background: '#001529' }}
      >
        <div
          style={{
            color: '#fff',
            padding: collapsed ? '20px 8px' : '20px 16px',
            textAlign: 'center',
            borderBottom: '1px solid #1f2d3d',
          }}
        >
          <div style={{ fontSize: collapsed ? 24 : 28 }}>📊</div>
          {!collapsed && (
            <>
              <div style={{ fontSize: 16, fontWeight: 600, marginTop: 6 }}>IALM</div>
              <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>资产负债管理智能分析</div>
            </>
          )}
        </div>
        <Menu
          mode="inline"
          theme="dark"
          selectedKeys={[selectedKey]}
          openKeys={openKeys}
          onOpenChange={(keys) => setOpenKeys(keys as string[])}
          items={menuItems}
          onClick={({ key }) => nav(key)}
          style={{ marginTop: 8, borderRight: 0 }}
        />
      </Sider>

      <Layout>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Space>
            <FileSearchOutlined style={{ color: '#667eea', fontSize: 18 }} />
            <Text strong style={{ fontSize: 16, color: '#667eea' }}>{currentLabel}</Text>
          </Space>
          <Dropdown menu={userMenu} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar style={{ background: '#667eea' }} icon={<UserOutlined />} />
              <Text>{user.real_name || user.username || 'User'}</Text>
            </Space>
          </Dropdown>
        </Header>

        <Content style={{ margin: 16, padding: 24, background: '#fff', borderRadius: 8, minHeight: 'calc(100vh - 180px)' }}>
          <Outlet />
        </Content>

        <Footer style={{ textAlign: 'center', background: 'transparent', padding: '16px 0' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            IALM 保险资产负债管理智能分析平台 v1.0.0 ·{' '}
            <a href="https://beian.miit.gov.cn/" target="_blank" rel="noreferrer">
              京ICP备2026054150号
            </a>
          </Text>
        </Footer>
      </Layout>
    </Layout>
  )
}