/**
 * IALM 资产端管理
 */
import { Card, Tabs, Tag, Space } from 'antd'
import DataListPage from '../components/DataListPage'
import { assetsApi } from '../api'

const riskColors: Record<string, string> = {
  LOW: 'green',
  MEDIUM: 'orange',
  HIGH: 'red',
  UNRATED: 'default',
}

export default function Assets() {
  return (
    <Tabs
      defaultActiveKey="holdings"
      type="card"
      items={[
        {
          key: 'holdings',
          label: '资产持仓',
          children: (
            <DataListPage
              title="资产持仓管理"
              subtitle="投资持仓清单（市值/久期/评级/到期日）"
              fetcher={(p) => assetsApi.holdings(p)}
              columns={[
                { title: '保单号/编号', dataIndex: 'holding_name', width: 200 },
                { title: '保险公司', dataIndex: 'company_name', width: 140 },
                { title: '分类', dataIndex: 'category_code', width: 80 },
                { title: '账面价值(万)', dataIndex: 'book_value', width: 140,
                  render: (v: number) => v?.toLocaleString() },
                { title: '市值(万)', dataIndex: 'market_value', width: 120,
                  render: (v: number) => v?.toLocaleString() },
                { title: '票面利率', dataIndex: 'coupon_rate', width: 100,
                  render: (v: number) => `${(v * 100).toFixed(2)}%` },
                { title: '久期(年)', dataIndex: 'duration_years', width: 100,
                  render: (v: number) => v?.toFixed(2) },
                { title: '到期日', dataIndex: 'maturity_date', width: 120 },
                { title: '评级', dataIndex: 'rating', width: 80,
                  render: (v: string) => v ? <Tag color="blue">{v}</Tag> : '-' },
                { title: '币种', dataIndex: 'currency', width: 80 },
              ]}
            />
          ),
        },
        {
          key: 'categories',
          label: '资产分类',
          children: (
            <DataListPage
              title="资产分类"
              subtitle="资产分类树（按风险等级划分）"
              fetcher={(p) => assetsApi.categories(p)}
              columns={[
                { title: '分类编码', dataIndex: 'category_code', width: 140 },
                { title: '分类名称', dataIndex: 'category_name' },
                { title: '父分类', dataIndex: 'parent_code', width: 120,
                  render: (v: string) => v || '根分类' },
                { title: '风险等级', dataIndex: 'risk_level', width: 120,
                  render: (v: string) => <Tag color={riskColors[v]}>{v}</Tag> },
              ]}
            />
          ),
        },
        {
          key: 'cashflows',
          label: '资产现金流',
          children: (
            <DataListPage
              title="资产现金流"
              subtitle="按年/月预测的资产端现金流"
              fetcher={(p) => assetsApi.cashflows({ ...p, page_size: 50 })}
              columns={[
                { title: '公司ID', dataIndex: 'company_id', width: 80 },
                { title: '持仓ID', dataIndex: 'holding_id', width: 100 },
                { title: '年', dataIndex: 'period_year', width: 80 },
                { title: '月', dataIndex: 'period_month', width: 80 },
                { title: '金额(万)', dataIndex: 'amount', width: 140,
                  render: (v: number) => v?.toLocaleString() },
                { title: '币种', dataIndex: 'currency', width: 80 },
              ]}
            />
          ),
        },
      ]}
    />
  )
}