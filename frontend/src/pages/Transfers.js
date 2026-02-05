import { useState, useEffect } from 'react'
import { transfersAPI, accountsAPI } from '../services/api'

export default function Transfers() {
  const [accounts, setAccounts] = useState([])
  const [fromAccountId, setFromAccountId] = useState('')
  const [toAccountId, setToAccountId] = useState('')
  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState('USD')
  const [loading, setLoading] = useState(true)
  const [transferring, setTransferring] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      const response = await accountsAPI.getAll()
      setAccounts(response.data)
      if (response.data.length > 0) {
        setFromAccountId(response.data[0].id.toString())
        setCurrency(response.data[0].currency)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load accounts')
    } finally {
      setLoading(false)
    }
  }

  const handleTransfer = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setTransferring(true)

    // Generate idempotency key
    const idempotencyKey = `transfer-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

    try {
      const response = await transfersAPI.transfer(
        {
          from_account_id: parseInt(fromAccountId),
          to_account_id: parseInt(toAccountId),
          amount: parseFloat(amount),
          currency,
        },
        idempotencyKey
      )
      setSuccess(`Transfer successful! Transaction ID: ${response.data.id}`)
      setAmount('')
      loadAccounts() // Refresh accounts to show updated balances
    } catch (err) {
      setError(err.response?.data?.detail || 'Transfer failed')
    } finally {
      setTransferring(false)
    }
  }

  const fromAccount = accounts.find((a) => a.id === parseInt(fromAccountId))

  const accountLabel = (account) => {
    const name = [account.first_name, account.last_name].filter(Boolean).join(' ')
    const holder = name ? ` (${name})` : ''
    return `${account.currency}${holder} — ${account.currency} ${parseFloat(account.balance).toFixed(2)}`
  }

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Transfer Money</h1>
        <p className="mt-2 text-gray-600">Transfer funds between accounts</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-6">
        <form onSubmit={handleTransfer} className="space-y-6">
          <div>
            <label htmlFor="fromAccount" className="block text-sm font-medium text-gray-700">
              From Account
            </label>
            <select
              id="fromAccount"
              value={fromAccountId}
              onChange={(e) => {
                setFromAccountId(e.target.value)
                const account = accounts.find((a) => a.id === parseInt(e.target.value))
                if (account) {
                  setCurrency(account.currency)
                }
              }}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
              required
            >
              <option value="">Select account</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {accountLabel(account)}
                </option>
              ))}
            </select>
            {fromAccount && (
              <p className="mt-1 text-sm text-gray-500">
                Available balance: {fromAccount.currency} {parseFloat(fromAccount.balance).toFixed(2)}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="toAccount" className="block text-sm font-medium text-gray-700">
              To Account
            </label>
            <select
              id="toAccount"
              value={toAccountId}
              onChange={(e) => setToAccountId(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
              required
            >
              <option value="">Select account</option>
              {accounts
                .filter((account) => account.id !== parseInt(fromAccountId))
                .map((account) => (
                  <option key={account.id} value={account.id}>
                    {accountLabel(account)}
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
              Amount ({currency})
            </label>
            <input
              type="number"
              id="amount"
              step="0.01"
              min="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              placeholder="0.00"
              required
            />
          </div>

          <button
            type="submit"
            disabled={transferring || !fromAccountId || !toAccountId || !amount}
            className="w-full inline-flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            {transferring ? 'Processing...' : 'Transfer Money'}
          </button>
        </form>
      </div>
    </div>
  )
}
