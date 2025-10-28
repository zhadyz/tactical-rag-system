'use client'

import React, { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { ChevronDown } from 'lucide-react'

interface DropdownItem {
  title: string
  href: string
  description: string
}

interface NavSection {
  title: string
  items: DropdownItem[]
}

const navSections: NavSection[] = [
  {
    title: 'Documentation',
    items: [
      {
        title: 'Get Started',
        href: '/getting-started/quick-start',
        description: 'Quick setup guide and installation'
      },
      {
        title: 'Core Concepts',
        href: '/core-concepts/gpu-acceleration',
        description: 'GPU acceleration, caching, and adaptive retrieval'
      },
      {
        title: 'API Reference',
        href: '/api-reference',
        description: 'Complete API documentation and endpoints'
      }
    ]
  },
  {
    title: 'Architecture',
    items: [
      {
        title: 'Overview',
        href: '/architecture/overview',
        description: 'System architecture and design principles'
      },
      {
        title: 'Backend',
        href: '/architecture/backend',
        description: 'FastAPI backend with GPU acceleration'
      },
      {
        title: 'Frontend',
        href: '/architecture/frontend',
        description: 'React frontend with streaming UI'
      },
      {
        title: 'Integration',
        href: '/architecture/integration',
        description: 'Cross-layer integration and data flow'
      }
    ]
  },
  {
    title: 'Resources',
    items: [
      {
        title: 'Benchmarks',
        href: '/benchmarks/overview',
        description: 'Performance metrics and comparisons'
      },
      {
        title: 'Advanced',
        href: '/advanced/deployment',
        description: 'Deployment, monitoring, and security'
      },
      {
        title: 'Interactive Demos',
        href: '/interactive-demos',
        description: 'Live demonstrations and visualizations'
      },
      {
        title: 'About',
        href: '/about',
        description: 'Project background and team information'
      }
    ]
  }
]

export function CustomNavbar() {
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null)
  const closeTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const handleMouseEnter = (sectionTitle: string) => {
    // CRITICAL: Clear any pending close timeout FIRST before showing dropdown
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current)
      closeTimeoutRef.current = null
    }
    // Immediately show the dropdown (even if re-hovering same one)
    setActiveDropdown(sectionTitle)
  }

  const handleMouseLeave = () => {
    // CRITICAL: Clear any existing timeout first to prevent race conditions
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current)
    }
    // Delay closing to allow mouse to move to dropdown
    closeTimeoutRef.current = setTimeout(() => {
      setActiveDropdown(null)
    }, 100)
  }

  const handleDropdownMouseEnter = () => {
    // CRITICAL: Clear close timeout when entering dropdown
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current)
      closeTimeoutRef.current = null
    }
  }

  const handleDropdownMouseLeave = () => {
    // Close dropdown when leaving dropdown area
    setActiveDropdown(null)
  }

  const handleLinkClick = () => {
    // Clear any pending timeout and close immediately
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current)
      closeTimeoutRef.current = null
    }
    setActiveDropdown(null)
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (closeTimeoutRef.current) {
        clearTimeout(closeTimeoutRef.current)
      }
    }
  }, [])

  return (
    <>
      <nav className="custom-navbar-wrapper relative">
        <ul className="flex items-center gap-1">
          {navSections.map((section) => (
            <li
              key={section.title}
              className="relative dropdown-container"
              onMouseEnter={() => handleMouseEnter(section.title)}
              onMouseLeave={handleMouseLeave}
            >
              <button
                className="flex items-center gap-1 rounded-md px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
                aria-expanded={activeDropdown === section.title}
              >
                {section.title}
                <ChevronDown
                  className={`h-4 w-4 transition-transform duration-200 ${
                    activeDropdown === section.title ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {/* Dropdown Menu */}
              {activeDropdown === section.title && (
                <div
                  className="dropdown-menu absolute left-0 top-full z-50 mt-1 w-80 rounded-lg border border-gray-200 bg-white p-2 shadow-xl dark:border-gray-800 dark:bg-gray-900"
                  onMouseEnter={handleDropdownMouseEnter}
                  onMouseLeave={handleDropdownMouseLeave}
                  style={{
                    animation: 'dropdown-enter 0.15s ease-out'
                  }}
                >
                  <ul className="space-y-1">
                    {section.items.map((item) => (
                      <li key={item.href}>
                        <Link
                          href={item.href}
                          className="block rounded-md p-3 transition-all hover:bg-gray-50 dark:hover:bg-gray-800"
                          onClick={handleLinkClick}
                        >
                          <div className="font-medium text-gray-900 dark:text-gray-100">
                            {item.title}
                          </div>
                          <div className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
                            {item.description}
                          </div>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </li>
          ))}
        </ul>
      </nav>

      <style jsx global>{`
        @keyframes dropdown-enter {
          from {
            opacity: 0;
            transform: translateY(-4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .dropdown-menu {
          backdrop-filter: blur(12px);
        }

        /* Ensure dropdown stays visible during hover transition */
        .dropdown-container {
          position: relative;
        }

        /* Ensure pointer events work correctly */
        .dropdown-menu,
        .dropdown-menu * {
          pointer-events: auto;
        }
      `}</style>
    </>
  )
}
