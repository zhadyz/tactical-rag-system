import { useRouter } from 'next/router'
import Link from 'next/link'
import { AlertCircle, Home, ArrowLeft } from 'lucide-react'

export default function AuthError() {
  const router = useRouter()
  const { error } = router.query

  const errorMessages: { [key: string]: { title: string; description: string } } = {
    Configuration: {
      title: 'Server Configuration Error',
      description: 'There is a problem with the server configuration. Please contact support.'
    },
    AccessDenied: {
      title: 'Access Denied',
      description: 'You do not have permission to sign in. Please contact an administrator.'
    },
    Verification: {
      title: 'Verification Failed',
      description: 'The verification token has expired or has already been used.'
    },
    OAuthSignin: {
      title: 'OAuth Sign-In Error',
      description: 'Error in constructing an authorization URL. Please try again.'
    },
    OAuthCallback: {
      title: 'OAuth Callback Error',
      description: 'Error in handling the response from the OAuth provider. Please try again.'
    },
    OAuthCreateAccount: {
      title: 'OAuth Account Creation Error',
      description: 'Could not create OAuth provider user in the database. Please try again.'
    },
    EmailCreateAccount: {
      title: 'Email Account Creation Error',
      description: 'Could not create email provider user in the database. Please try again.'
    },
    Callback: {
      title: 'Callback Error',
      description: 'Error in the OAuth callback handler route. Please try again.'
    },
    OAuthAccountNotLinked: {
      title: 'Account Not Linked',
      description: 'This email is already associated with another account. Please sign in with your original provider.'
    },
    EmailSignin: {
      title: 'Email Sign-In Error',
      description: 'The email could not be sent. Please try again.'
    },
    CredentialsSignin: {
      title: 'Sign-In Error',
      description: 'Sign in failed. Check the details you provided are correct.'
    },
    Default: {
      title: 'Authentication Error',
      description: 'An unexpected error occurred. Please try again.'
    }
  }

  const errorInfo = errorMessages[error as string] || errorMessages.Default

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4 dark:from-gray-950 dark:to-gray-900">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-3 mb-6">
            <img src="/apollo-logo.png" alt="Apollo" className="h-16 w-16" />
          </Link>
        </div>

        {/* Error Card */}
        <div className="rounded-2xl border border-red-200 bg-white p-8 shadow-lg dark:border-red-900/50 dark:bg-gray-900">
          {/* Icon */}
          <div className="mb-6 flex justify-center">
            <div className="rounded-full bg-red-100 p-4 dark:bg-red-900/30">
              <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
            </div>
          </div>

          {/* Error Message */}
          <div className="mb-6 text-center">
            <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
              {errorInfo.title}
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              {errorInfo.description}
            </p>
          </div>

          {/* Error Code */}
          {error && (
            <div className="mb-6 rounded-lg bg-gray-100 p-3 dark:bg-gray-800">
              <p className="text-center text-sm text-gray-600 dark:text-gray-400">
                Error Code: <span className="font-mono font-semibold">{error}</span>
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="space-y-3">
            <Link
              href="/auth/signin"
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition-all hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
            >
              <ArrowLeft className="h-4 w-4" />
              Try Again
            </Link>
            <Link
              href="/"
              className="flex w-full items-center justify-center gap-2 rounded-lg border-2 border-gray-300 bg-white px-6 py-3 font-medium text-gray-700 transition-all hover:border-gray-400 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-gray-600 dark:hover:bg-gray-700 dark:focus:ring-offset-gray-900"
            >
              <Home className="h-4 w-4" />
              Return Home
            </Link>
          </div>
        </div>

        {/* Support Link */}
        <p className="mt-8 text-center text-sm text-gray-600 dark:text-gray-400">
          Need help?{' '}
          <a
            href="mailto:contact@onyxlab.ai"
            className="text-blue-600 hover:underline dark:text-blue-400"
          >
            Contact Support
          </a>
        </p>
      </div>
    </div>
  )
}
