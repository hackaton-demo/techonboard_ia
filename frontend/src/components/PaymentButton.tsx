import { useState } from 'react'
import { CheckCircle, Loader2, XCircle, CreditCard, ExternalLink, Zap } from 'lucide-react'
import clsx from 'clsx'
import type { PaymentRequest } from '@/types'
import { verifyPayment } from '@/lib/api'

type PaymentState = 'idle' | 'processing' | 'success' | 'error'
type PaymentMode = 'wallet' | 'demo'

interface PaymentButtonProps {
  paymentRequest: PaymentRequest
  onSuccess: () => void
  onError?: (error: string) => void
}

function truncateAddress(address: string): string {
  if (address.length <= 12) return address
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

function networkLabel(network: string): string {
  const map: Record<string, string> = {
    'eip155:84532': 'Base Sepolia (testnet)',
    'eip155:8453': 'Base Mainnet',
  }
  return map[network] ?? network
}

export function PaymentButton({ paymentRequest, onSuccess, onError }: PaymentButtonProps) {
  const [state, setState] = useState<PaymentState>('idle')
  const [mode, setMode] = useState<PaymentMode>('demo')
  const [txHash, setTxHash] = useState('demo_hackathon_2026')
  const [showTxInput, setShowTxInput] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const handleOpenWallet = () => {
    if (paymentRequest.payment_url) {
      window.open(paymentRequest.payment_url, '_blank', 'noopener,noreferrer')
    }
    setShowTxInput(true)
  }

  const handleDemoPay = () => {
    setTxHash('demo_hackathon_2026')
    setShowTxInput(true)
  }

  const handleVerify = async () => {
    setState('processing')
    try {
      const verified = await verifyPayment(txHash)
      if (verified) {
        setState('success')
        setTimeout(() => onSuccess(), 900)
      } else {
        setState('error')
        setErrorMessage('Transaction not verified. Please try again.')
        onError?.('Payment verification failed')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error verifying the payment'
      setState('error')
      setErrorMessage(message)
      onError?.(message)
    }
  }

  if (state === 'success') {
    return (
      <div className="rounded-xl border border-emerald-800/50 bg-emerald-950/40 p-5 flex items-center justify-center gap-2 text-emerald-400">
        <CheckCircle size={20} />
        <span className="font-medium">Payment verified — starting onboarding</span>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/80 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 text-indigo-400">
        <CreditCard size={18} />
        <span className="text-sm font-semibold">x402 Payment Required</span>
        <span className="ml-auto text-xs text-gray-600 font-mono">HTTP 402</span>
      </div>

      {/* Payment details */}
      <div className="space-y-1.5 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-gray-500">Amount</span>
          <span className="font-bold text-white">
            {paymentRequest.amount_usdc}{' '}
            <span className="text-indigo-400 font-normal">USDC</span>
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-500">Destination</span>
          <span className="font-mono text-gray-300 text-xs">{truncateAddress(paymentRequest.wallet_address)}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-500">Network</span>
          <span className="text-gray-300 text-xs">{networkLabel(paymentRequest.network)}</span>
        </div>
      </div>

      {/* Mode selector */}
      {!showTxInput && (
        <div className="grid grid-cols-2 gap-2 pt-1">
          {/* Real wallet payment */}
          <button
            onClick={() => { setMode('wallet'); handleOpenWallet() }}
            className="flex flex-col items-center gap-1 py-3 px-2 rounded-lg border border-indigo-700/60 bg-indigo-900/30 hover:bg-indigo-900/50 transition-colors text-indigo-300 hover:text-indigo-200"
          >
            <ExternalLink size={16} />
            <span className="text-xs font-medium">Pay with Wallet</span>
            <span className="text-[10px] text-indigo-500">Real USDC on Base</span>
          </button>

          {/* Demo payment */}
          <button
            onClick={() => { setMode('demo'); handleDemoPay() }}
            className="flex flex-col items-center gap-1 py-3 px-2 rounded-lg border border-purple-700/60 bg-purple-900/30 hover:bg-purple-900/50 transition-colors text-purple-300 hover:text-purple-200"
          >
            <Zap size={16} />
            <span className="text-xs font-medium">Demo Pay</span>
            <span className="text-[10px] text-purple-500">Hackathon mode</span>
          </button>
        </div>
      )}

      {/* TX Hash input */}
      {showTxInput && (
        <div className="space-y-2">
          <label className="text-xs text-gray-500 block">
            {mode === 'wallet'
              ? 'Paste the transaction hash from your wallet'
              : 'Demo hash (accepts any demo_*)'}
          </label>
          <input
            type="text"
            value={txHash}
            onChange={(e) => setTxHash(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 font-mono focus:outline-none focus:border-indigo-500 transition-colors"
            placeholder={mode === 'wallet' ? '0x...' : 'demo_...'}
            disabled={state === 'processing'}
          />
        </div>
      )}

      {/* Error */}
      {state === 'error' && errorMessage && (
        <div className="flex items-center gap-2 text-red-400 text-xs">
          <XCircle size={13} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Confirm button */}
      {showTxInput && (
        <button
          onClick={() => void handleVerify()}
          disabled={state === 'processing' || !txHash.trim()}
          className={clsx(
            'w-full py-2.5 px-4 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-all duration-200',
            state === 'processing'
              ? 'bg-indigo-700/50 text-indigo-300 cursor-not-allowed'
              : state === 'error'
              ? 'bg-red-600 hover:bg-red-500 text-white'
              : 'bg-indigo-600 hover:bg-indigo-500 text-white'
          )}
        >
          {state === 'processing' ? (
            <>
              <Loader2 size={15} className="animate-spin" />
              <span>Verifying with x402...</span>
            </>
          ) : (
            'Confirm Payment'
          )}
        </button>
      )}

      {/* x402 badge */}
      <div className="flex items-center justify-center gap-1.5 text-[10px] text-gray-700 pt-1">
        <span>Powered by</span>
        <span className="font-mono text-gray-600">x402 protocol</span>
        <span>·</span>
        <span>Coinbase Base</span>
      </div>
    </div>
  )
}
