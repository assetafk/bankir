import { useState, useEffect } from 'react'
import { accountsAPI } from '../services/api'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      const response = await accountsAPI.getAll()
      setAccounts(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load accounts')
    } finally {
      setLoading(false)
    }
  }

  const totalBalance = accounts.reduce((sum, account) => {
    return sum + parseFloat(account.balance || 0)
  }, 0)

  const heroCards = [
    { label: 'Надёжность', desc: 'Ваши средства под защитой', icon: '🛡️', gradient: 'from-emerald-500/20 to-teal-600/20 dark:from-emerald-500/30 dark:to-teal-600/30', border: 'border-emerald-500/30' },
    { label: 'Скорость', desc: 'Мгновенные переводы', icon: '⚡', gradient: 'from-amber-500/20 to-orange-600/20 dark:from-amber-500/30 dark:to-orange-600/30', border: 'border-amber-500/30' },
    { label: 'Простота', desc: 'Удобный интерфейс', icon: '✨', gradient: 'from-violet-500/20 to-purple-600/20 dark:from-violet-500/30 dark:to-purple-600/30', border: 'border-violet-500/30' },
  ]

  if (loading) {
    return (
      <div className="text-center py-8 text-gray-600 dark:text-gray-400">Loading...</div>
    )
  }

  return (
    <div>
      {/* Hero widget with "bankir" */}
      <section className="mb-10 rounded-2xl overflow-hidden bg-gradient-to-br from-slate-100 to-slate-200 dark:from-gray-800 dark:to-gray-900 shadow-xl">
        <div className="px-6 py-10 sm:px-10 sm:py-14 text-center">
          <h1 className="font-display text-5xl sm:text-6xl md:text-7xl font-semibold tracking-tight text-gray-900 dark:text-white drop-shadow-sm">
            bankir
          </h1>
          <p className="mt-3 text-lg text-gray-600 dark:text-gray-400 max-w-md mx-auto">
            Ваш надёжный банк в цифре
          </p>
          <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-3xl mx-auto">
            {heroCards.map((card) => (
              <div
                key={card.label}
                className={`rounded-xl bg-gradient-to-br ${card.gradient} backdrop-blur border ${card.border} p-4 shadow-lg transition transform hover:scale-[1.02] hover:shadow-xl`}
              >
                <span className="text-2xl block mb-2">{card.icon}</span>
                <div className="font-semibold text-gray-800 dark:text-gray-100">{card.label}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">{card.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h2>
        <p className="mt-1 text-gray-600 dark:text-gray-400">Welcome to your banking dashboard</p>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 mb-8">
        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-xl border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">💰</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total Balance</dt>
                  <dd className="text-2xl font-semibold text-gray-900 dark:text-white">
                    ${totalBalance.toFixed(2)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-xl border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">🏦</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total Accounts</dt>
                  <dd className="text-2xl font-semibold text-gray-900 dark:text-white">{accounts.length}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-xl border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">💸</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Currencies</dt>
                  <dd className="text-2xl font-semibold text-gray-900 dark:text-white">
                    {new Set(accounts.map((a) => a.currency)).size}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow rounded-xl border border-gray-200 dark:border-gray-700">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Recent Accounts</h2>
            <Link
              to="/accounts"
              className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 text-sm font-medium"
            >
              View all →
            </Link>
          </div>
          {accounts.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400 mb-4">No accounts yet</p>
              <Link
                to="/accounts"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600"
              >
                Create Account
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
                <thead className="bg-gray-50 dark:bg-gray-700/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Holder
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Currency
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Balance
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Created
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                  {accounts.slice(0, 5).map((account) => (
                    <tr key={account.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {[account.first_name, account.last_name].filter(Boolean).join(' ') || '—'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {account.currency}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {account.currency} {parseFloat(account.balance).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {new Date(account.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
