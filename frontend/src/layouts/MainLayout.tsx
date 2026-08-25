/**
 * IALM 主布局
 */
import { useState, useEffect } from 'react'
import { Layout, Menu, Avatar, Dropdown, Space, Typography } from 'antd'
import {
  DashboardOutlined,
  BankOutlined,
  LineChartOutlined,
  CalculatorOutlined,
  HistoryOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const { Header, Sider, Content, Footer } = Layout
const { Text } = Typography

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '工作台' },
  { key: '/companies', icon: <BankOutlined />, label: '保险公司' },
  { key: '/match', icon: <LineChartOutlined />, label: '5号规则分析' },
  { key: '/algorithms', icon: <CalculatorOutlined />, label: '算法引擎' },
  { key: '/history', icon: <HistoryOutlined />, label: '分析历史' },
]

export default function MainLayout() {
  const nav = useNavigate()
  const loc = useLocation()
  const [user, setUser] = useState<any>({})

  useEffect(() => {
    const stored = localStorage.getItem('ialm_user')
    if (stored) {
      try {
        setUser(JSON.parse(stored))
      } catch {}
    }
  }, [])

  const selectedKey = menuItems.find((m) => loc.pathname.startsWith(m.key))?.key || '/dashboard'

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
      <Sider width={220} style={{ background: '#001529' }}>
        <div
          style={{
            color: '#fff',
            padding: '20px 16px',
            textAlign: 'center',
            borderBottom: '1px solid #1f2d3d',
          }}
        >
          <div style={{ fontSize: 28 }}>📊</div>
          <div style={{ fontSize: 16, fontWeight: 600, marginTop: 6 }}>IALM</div>
          <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>资产负债管理智能分析</div>
        </div>
        <Menu
          mode="Style"
          theme="dark"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => nav(key)}
          style={{ marginTop: 8 }}
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
          <div style={{ fontSize: 18, fontWeight: 600, color: '#667eea' }}>
            {menuItems.find((m) => m.key === selectedKey)?.label}
          </div>
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