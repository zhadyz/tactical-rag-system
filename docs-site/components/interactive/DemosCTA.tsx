import React from 'react'

export function DemosCTA() {
  return (
    <div className="mx-auto my-20 max-w-4xl rounded-2xl border border-blue-200/50 bg-gradient-to-br from-blue-50 to-blue-100/30 p-12 text-center dark:border-blue-800/30 dark:from-blue-950/30 dark:to-blue-900/20">
      <h2 className="mb-4 text-3xl font-bold text-gray-900 dark:text-white">
        Ready to Experience Apollo?
      </h2>
      <p className="mx-auto mb-8 max-w-2xl text-lg text-gray-700 dark:text-gray-300">
        These interactive demos just scratch the surface. Try Apollo with your own data and see the difference GPU acceleration makes.
      </p>
      <div className="flex flex-wrap justify-center gap-4">
        <a
          href="/getting-started/quick-start"
          className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-4 font-bold text-white shadow-lg transition-all hover:scale-105 hover:bg-blue-700 hover:shadow-2xl"
        >
          Get Started
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </a>
        <a
          href="https://github.com/yourusername/apollo-rag"
          className="inline-flex items-center gap-2 rounded-xl border-2 border-gray-300 bg-white px-8 py-4 font-bold text-gray-900 shadow-lg transition-all hover:scale-105 hover:border-gray-400 hover:shadow-2xl dark:border-gray-700 dark:bg-gray-900 dark:text-white dark:hover:border-gray-600"
        >
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
            <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
          </svg>
          View on GitHub
        </a>
      </div>
    </div>
  )
}
