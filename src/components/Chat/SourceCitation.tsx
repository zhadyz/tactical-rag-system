import React, { useState, useMemo, useCallback } from 'react';
import { FileText, ChevronDown, ChevronRight, BookOpen, ExternalLink } from 'lucide-react';
import type { Source } from '../../types';
import { PDFViewerModal } from '../PDFViewer';

interface SourceCitationProps {
  source: Source;
  index: number;
}

// PERFORMANCE OPTIMIZATION: Memoized helper functions moved outside component
// These are pure functions that don't depend on component state

// Handle multiple field names for source content
const getSourceContent = (src: Source): string => {
  // Try different field names that backends might use
  if (src.content) return src.content;
  if (src.excerpt) return src.excerpt;
  if (src.page_content) return src.page_content;
  return 'No content available';
};

// Get relevance score from different possible locations
const getRelevanceScore = (src: Source): number => {
  // Try metadata.score first (standard location)
  if (src.metadata?.score !== undefined) return src.metadata.score;
  // Fallback to top-level relevance_score
  if (src.relevance_score !== undefined) return src.relevance_score;
  // Default to 0 if not found
  return 0;
};

const formatScore = (score: number): string => {
  return (score * 100).toFixed(1);
};

// Determine relevance badge styling based on score
const getRelevanceBadge = (score: number) => {
  if (score > 0.8) {
    return {
      color: 'bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400 border-success-200 dark:border-success-800/50',
      label: 'High relevance',
    };
  } else if (score > 0.6) {
    return {
      color: 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400 border-warning-200 dark:border-warning-800/50',
      label: 'Medium relevance',
    };
  } else {
    return {
      color: 'bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-400 border-neutral-200 dark:border-neutral-700',
      label: 'Lower relevance',
    };
  }
};

// PERFORMANCE OPTIMIZATION: Wrap component with React.memo for shallow prop comparison
export const SourceCitation = React.memo<SourceCitationProps>(({
  source,
  index,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isPDFViewerOpen, setIsPDFViewerOpen] = useState(false);

  // PERFORMANCE OPTIMIZATION: Memoize computed values
  const relevanceScore = useMemo(() => getRelevanceScore(source), [source]);
  const relevanceBadge = useMemo(() => getRelevanceBadge(relevanceScore), [relevanceScore]);
  const sourceContent = useMemo(() => getSourceContent(source), [source]);
  const formattedScore = useMemo(() => formatScore(relevanceScore), [relevanceScore]);

  // PERFORMANCE OPTIMIZATION: Memoize event handlers with useCallback
  const handleToggleExpanded = useCallback(() => {
    setIsExpanded(prev => !prev);
  }, []);

  const handleOpenPDF = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent expanding/collapsing the citation
    setIsPDFViewerOpen(true);
  }, []);

  const handleClosePDF = useCallback(() => {
    setIsPDFViewerOpen(false);
  }, []);

  return (
    <div className="group/citation border border-neutral-200 dark:border-neutral-800 rounded-xl overflow-hidden
                    transition-all duration-200 hover:border-neutral-300 dark:hover:border-neutral-700
                    hover:shadow-md bg-white dark:bg-neutral-900">
      {/* Header */}
      <button
        onClick={handleToggleExpanded}
        className="w-full flex items-center gap-3 p-4 hover:bg-neutral-50/50 dark:hover:bg-neutral-800/50
                   transition-all duration-150 text-left group/button"
      >
        {/* Expand icon */}
        <div className="flex-shrink-0 transition-transform duration-200 group-hover/button:scale-110">
          {isExpanded ? (
            <ChevronDown size={18} className="text-neutral-500 dark:text-neutral-400" />
          ) : (
            <ChevronRight size={18} className="text-neutral-500 dark:text-neutral-400" />
          )}
        </div>

        {/* File icon */}
        <div className="flex-shrink-0 w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-lg
                        flex items-center justify-center transition-all duration-200
                        group-hover/button:bg-primary-200 dark:group-hover/button:bg-primary-900/50
                        group-hover/button:scale-105">
          <FileText size={16} className="text-primary-600 dark:text-primary-400" strokeWidth={2} />
        </div>

        {/* File info */}
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-center gap-2">
            <span
              onClick={handleOpenPDF}
              className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 truncate
                         hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer
                         transition-colors duration-150 flex items-center gap-1.5 group/link"
              title="Click to open PDF"
            >
              <span className="truncate">{source.metadata.source}</span>
              <ExternalLink
                size={14}
                className="flex-shrink-0 opacity-0 group-hover/link:opacity-100 transition-opacity duration-150"
              />
            </span>
          </div>
          {source.metadata.page && (
            <div className="flex items-center gap-1.5 text-xs text-neutral-500 dark:text-neutral-400">
              <BookOpen size={12} />
              <span className="font-medium">Page {source.metadata.page}</span>
            </div>
          )}
        </div>

        {/* Relevance badge */}
        <div className="flex-shrink-0">
          <span
            className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg font-semibold
                       border transition-all duration-150 ${relevanceBadge.color}`}
            title={relevanceBadge.label}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60"></span>
            {formattedScore}%
          </span>
        </div>
      </button>

      {/* Expandable content */}
      {isExpanded && (
        <div className="px-4 pb-4 animate-slide-up">
          <div className="pt-3 border-t border-neutral-200 dark:border-neutral-800">
            {/* Content preview */}
            <div className="bg-neutral-50 dark:bg-neutral-900/50 rounded-xl p-4 border border-neutral-200 dark:border-neutral-800">
              <p className="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed whitespace-pre-wrap">
                {sourceContent}
              </p>
            </div>
            {/* Optional: Metadata footer */}
            <div className="mt-3 flex items-center gap-4 text-xs text-neutral-500 dark:text-neutral-400">
              <span className="flex items-center gap-1">
                <span className="font-medium">Source {index + 1}</span>
              </span>
              <span className="flex items-center gap-1">
                <span className="w-1 h-1 rounded-full bg-neutral-400 dark:bg-neutral-600"></span>
                <span>{relevanceBadge.label}</span>
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Elegant PDF Viewer Modal */}
      <PDFViewerModal
        isOpen={isPDFViewerOpen}
        onClose={handleClosePDF}
        pdfPath={source.metadata.filePath || source.file_name || source.metadata.source}
        initialPage={source.metadata.page || 1}
        highlightText={sourceContent}
        fileName={source.file_name || source.metadata.source}
      />
    </div>
  );
});
