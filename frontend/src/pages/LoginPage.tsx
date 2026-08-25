/**
 * IALM 登录页（沿用 4 模块蓝紫渐变风格 #667eea → #764ba2）
 */
import { useState } from 'react'
import { Form, Input, Button, Card, message, Typography } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api'

const { Title, Text } = Typography

export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const nav = useNavigate()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const res = await authApi.login(values.username, values.password)
      const { access_token, user } = res.data
      localStorage.setItem('ialm_token', access_token)
      localStorage.setItem('ialm_user', JSON.stringify(user))
      message.success(`欢迎，${user.real_name || user.username}`)
      nav('/dashboard')
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '登录失败')
    }
    setLoading(false)
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
      }}
    >
      <Card
        style={{
          width: 420,
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
          borderRadius: 12,
        }}
        styles={{ body: { padding: 40 } }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>📊</div>
          <Title level={3} style={{ margin: 0, color: '#667eea' }}>
            IALM 保险资产负债管理
          </Title>
          <Text type="secondary">智能分析平台 · 5 号规则监管驱动</Text>
        </div>

        <Form onFinish={onFinish} size="large" layout="vertical">
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none',
                height: 44,
                fontSize: 16,
              }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', color: '#999', fontSize: 12, marginTop: 16 }}>
          <Text type="secondary">默认账号：admin / admin123</Text>
        </div>
      </Card>

      <div
        style={{
          position: 'fixed',
          bottom: 16,
          left: 0,
          right: 0,
          textAlign: 'center',
          color: 'rgba(255,255,255,0.85)',
          fontSize: 12,
        }}
      >
        <a
          href="https://beian.miit.gov.cn/"
          target="_blank"
          rel="noreferrer"
          style={{ color: 'rgba(255,255,255,0.85)' }}
        >
          京ICP备2026054150号
        </a>
      </div>
    </div>
  )
}