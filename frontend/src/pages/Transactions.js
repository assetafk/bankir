import { useState, useEffect } from 'react'
import { transactionsAPI, accountsAPI } from '../services/api'

export default function Transactions() {
  const [transactions, setTransactions] = useState([])
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({
    account_id: '',
    status: '',
    page: 1,
    page_size: 20,
  })

  useEffect(() => {
    loadAccounts()
  }, [])

  useEffect(() => {
    loadTransactions()
  }, [filters])

  const loadAccounts = async () => {
    try {
      const response = await accountsAPI.getAll()
      setAccounts(response.data)
    } catch (err) {
      console.error('Failed to load accounts:', err)
    }
  }

  const loadTransactions = async () => {
    setLoading(true)
    try {
      const params = {}
      if (filters.account_id) params.account_id = parseInt(filters.account_id)
      if (filters.status) params.status = filters.status
      params.page = filters.page
      params.page_size = filters.page_size

      const response = await transactionsAPI.getHistory(params)
      setTransactions(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load transactions')
    } finally {
      setLoading(false)
    }
  }

  const getAccountCurrency = (accountId) => {
    const account = accounts.find((a) => a.id === accountId)
    return account ? account.currency : 'N/A'
  }

  if (loading && transactions.length === 0) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Transaction History</h1>
        <p className="mt-2 text-gray-600">View all your transactions</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Filters</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label htmlFor="accountFilter" className="block text-sm font-medium text-gray-700">
              Account
            </label>
            <select
              id="accountFilter"
              value={filters.account_id}
              onChange={(e) => setFilters({ ...filters, account_id: e.target.value, page: 1 })}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
            >
              <option value="">All Accounts</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.currency} - #{account.id}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="statusFilter" className="block text-sm font-medium text-gray-700">
              Status
            </label>
            <select
              id="statusFilter"
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ account_id: '', status: '', page: 1, page_size: 20 })}
              className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {transactions.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No transactions found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    From
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    To
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{transaction.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.from_account_id ? (
                        <>
                          Account #{transaction.from_account_id}
                          <br />
                          <span className="text-xs text-gray-400">
                            {getAccountCurrency(transaction.from_account_id)}
                          </span>
                        </>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Account #{transaction.to_account_id}
                      <br />
                      <span className="text-xs text-gray-400">
                        {getAccountCurrency(transaction.to_account_id)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transaction.currency} {parseFloat(transaction.amount).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          transaction.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : transaction.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {transaction.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(transaction.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
