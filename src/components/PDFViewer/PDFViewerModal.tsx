import React, { useState, useEffect, useRef } from 'react';
import { X, ZoomIn, ZoomOut, ChevronLeft, ChevronRight, Maximize2, Minimize2 } from 'lucide-react';
import * as pdfjsLib from 'pdfjs-dist';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';
import { convertFileSrc } from '@tauri-apps/api/core';
import { PDF_VIEWER } from '../../constants/ui';

// Configure PDF.js worker - use unpkg for better compatibility
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;

interface PDFViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  pdfPath: string;
  initialPage?: number;
  highlightText?: string;
  fileName: string;
}

interface HighlightPosition {
  x: number;
  y: number;
  width: number;
  height: number;
}

export const PDFViewerModal: React.FC<PDFViewerModalProps> = ({
  isOpen,
  onClose,
  pdfPath,
  initialPage = 1,
  highlightText,
  fileName,
}) => {
  const [pdfDoc, setPdfDoc] = useState<PDFDocumentProxy | null>(null);
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [totalPages, setTotalPages] = useState(0);
  const [zoom, setZoom] = useState(PDF_VIEWER.DEFAULT_ZOOM);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [highlightPositions, setHighlightPositions] = useState<HighlightPosition[]>([]);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const textLayerRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Focus trap - focus close button when modal opens
  useEffect(() => {
    if (isOpen && closeButtonRef.current) {
      closeButtonRef.current.focus();
    }
  }, [isOpen]);

  // Load PDF document
  useEffect(() => {
    if (!isOpen) return;

    const loadPDF = async () => {
      try {
        setIsLoading(true);
        if (import.meta.env.DEV) {
          console.log('[PDFViewer] Loading PDF:', pdfPath);
        }

        // Convert Windows file path to Tauri asset URL
        const assetUrl = convertFileSrc(pdfPath);
        if (import.meta.env.DEV) {
          console.log('[PDFViewer] Converted to asset URL:', assetUrl);
        }

        const loadingTask = pdfjsLib.getDocument(assetUrl);
        const pdf = await loadingTask.promise;

        setPdfDoc(pdf);
        setTotalPages(pdf.numPages);
        setCurrentPage(initialPage);
        if (import.meta.env.DEV) {
          console.log('[PDFViewer] PDF loaded successfully. Pages:', pdf.numPages);
        }
      } catch (error) {
        if (import.meta.env.DEV) {
          console.error('[PDFViewer] Error loading PDF:', error);
          console.error('[PDFViewer] PDF Path:', pdfPath);
        }
        // Don't use alert - just log the error
      } finally {
        setIsLoading(false);
      }
    };

    loadPDF();
  }, [isOpen, pdfPath, initialPage]);

  // Render current page
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return;

    const renderPage = async () => {
      try {
        const page = await pdfDoc.getPage(currentPage);
        const canvas = canvasRef.current!;
        const context = canvas.getContext('2d')!;

        const viewport = page.getViewport({ scale: zoom * PDF_VIEWER.SCALE_MULTIPLIER });

        canvas.height = viewport.height;
        canvas.width = viewport.width;

        const renderContext = {
          canvasContext: context,
          viewport: viewport,
        };

        await page.render(renderContext).promise;

        // Render text layer for highlighting
        if (textLayerRef.current && highlightText) {
          await renderTextLayer(page, viewport);
        }
      } catch (error) {
        if (import.meta.env.DEV) {
          console.error('[PDFViewer] Error rendering page:', error);
        }
      }
    };

    renderPage();
  }, [pdfDoc, currentPage, zoom]);

  // Render text layer and find highlight position
  const renderTextLayer = async (page: PDFPageProxy, viewport: any) => {
    try {
      const textContent = await page.getTextContent();
      const textLayer = textLayerRef.current!;

      // Clear previous text layer
      textLayer.innerHTML = '';
      textLayer.style.left = canvasRef.current!.offsetLeft + 'px';
      textLayer.style.top = canvasRef.current!.offsetTop + 'px';
      textLayer.style.height = viewport.height + 'px';
      textLayer.style.width = viewport.width + 'px';

      // Find text matching highlight
      if (highlightText) {
        const searchText = highlightText.toLowerCase().trim().substring(0, PDF_VIEWER.MAX_HIGHLIGHT_TEXT_LENGTH);
        const items = textContent.items as any[];

        // Build full text with character position tracking
        let fullText = '';
        const itemPositions: { start: number; end: number; item: any }[] = [];

        items.forEach((item) => {
          const start = fullText.length;
          fullText += item.str;
          const end = fullText.length;
          itemPositions.push({ start, end, item });
          fullText += ' '; // Space between items
        });

        // Find the search text in the full text
        const searchStartIndex = fullText.toLowerCase().indexOf(searchText);

        if (searchStartIndex !== -1) {
          const searchEndIndex = searchStartIndex + searchText.length;
          const highlightBoxes: HighlightPosition[] = [];

          // Find all items that overlap with the search range
          for (const { start, end, item } of itemPositions) {
            // Check if this item overlaps with the search range
            if (end > searchStartIndex && start < searchEndIndex) {
              const transform = item.transform;

              // Calculate position and dimensions
              // PDF coordinates: transform[4] = x, transform[5] = y (bottom-left origin)
              // Canvas coordinates: need to flip y-axis
              const x = transform[4];
              const y = viewport.height - transform[5];

              // Estimate width based on item string length and font size
              // transform[0] is the horizontal scaling (font size related)
              const fontSize = transform[3] || 12;
              const itemWidth = item.width || (item.str.length * fontSize * 0.6);
              const itemHeight = fontSize * 1.2;

              highlightBoxes.push({
                x,
                y: y - itemHeight, // Adjust y to top of text
                width: itemWidth,
                height: itemHeight,
              });
            }
          }

          // Merge overlapping or adjacent highlight boxes on the same line
          const mergedBoxes = mergeHighlightBoxes(highlightBoxes);
          setHighlightPositions(mergedBoxes);

          if (import.meta.env.DEV) {
            console.log('[PDFViewer] Found', mergedBoxes.length, 'highlight boxes for text:', searchText.substring(0, 50));
          }
        } else {
          setHighlightPositions([]);
        }
      }
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('[PDFViewer] Error rendering text layer:', error);
      }
    }
  };

  // Merge highlight boxes that are on the same line
  const mergeHighlightBoxes = (boxes: HighlightPosition[]): HighlightPosition[] => {
    if (boxes.length === 0) return [];

    // Sort boxes by y position (top to bottom) then x position (left to right)
    const sorted = [...boxes].sort((a, b) => {
      const yDiff = a.y - b.y;
      if (Math.abs(yDiff) < 5) { // Same line threshold
        return a.x - b.x;
      }
      return yDiff;
    });

    const merged: HighlightPosition[] = [];
    let current = { ...sorted[0] };

    for (let i = 1; i < sorted.length; i++) {
      const box = sorted[i];

      // Check if boxes are on the same line and adjacent/overlapping
      const onSameLine = Math.abs(box.y - current.y) < 5;
      const adjacent = box.x <= current.x + current.width + 10; // Small gap tolerance

      if (onSameLine && adjacent) {
        // Merge boxes
        const rightEdge = Math.max(current.x + current.width, box.x + box.width);
        current.width = rightEdge - current.x;
        current.height = Math.max(current.height, box.height);
      } else {
        // Start new box
        merged.push(current);
        current = { ...box };
      }
    }

    merged.push(current);
    return merged;
  };

  // Keyboard shortcuts
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft' && currentPage > 1) setCurrentPage(currentPage - 1);
      if (e.key === 'ArrowRight' && currentPage < totalPages) setCurrentPage(currentPage + 1);
      if (e.key === '+' || e.key === '=') setZoom(Math.min(zoom + PDF_VIEWER.ZOOM_STEP, PDF_VIEWER.MAX_ZOOM));
      if (e.key === '-') setZoom(Math.max(zoom - PDF_VIEWER.ZOOM_STEP, PDF_VIEWER.MIN_ZOOM));
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isOpen, currentPage, totalPages, zoom, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="pdf-viewer-title"
      aria-describedby="pdf-viewer-description"
    >
      {/* Modal Container */}
      <div
        ref={containerRef}
        className={`relative bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl overflow-hidden
                    transform transition-all duration-300 ease-out animate-scale-in
                    ${isFullscreen ? 'w-full h-full' : 'w-[90vw] h-[90vh] max-w-7xl'}`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-white/95 dark:from-neutral-900/95 to-transparent backdrop-blur-md border-b border-neutral-200 dark:border-neutral-800">
          <div className="flex items-center justify-between p-4">
            {/* Title */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-xl flex items-center justify-center" aria-hidden="true">
                <svg className="w-5 h-5 text-primary-600 dark:text-primary-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                </svg>
              </div>
              <div className="min-w-0">
                <h3 id="pdf-viewer-title" className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 truncate">
                  {fileName}
                </h3>
                <p id="pdf-viewer-description" className="text-sm text-neutral-500 dark:text-neutral-400">
                  Page {currentPage} of {totalPages}
                </p>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2" role="toolbar" aria-label="PDF viewer controls">
              {/* Zoom Controls */}
              <button
                onClick={() => setZoom(Math.max(zoom - PDF_VIEWER.ZOOM_STEP, PDF_VIEWER.MIN_ZOOM))}
                disabled={zoom <= PDF_VIEWER.MIN_ZOOM}
                className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Zoom Out (-)"
                aria-label="Zoom out"
              >
                <ZoomOut size={20} className="text-neutral-700 dark:text-neutral-300" />
              </button>
              <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300 min-w-[60px] text-center" aria-label={`Current zoom level ${Math.round(zoom * 100)} percent`}>
                {Math.round(zoom * 100)}%
              </span>
              <button
                onClick={() => setZoom(Math.min(zoom + PDF_VIEWER.ZOOM_STEP, PDF_VIEWER.MAX_ZOOM))}
                disabled={zoom >= PDF_VIEWER.MAX_ZOOM}
                className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Zoom In (+)"
                aria-label="Zoom in"
              >
                <ZoomIn size={20} className="text-neutral-700 dark:text-neutral-300" />
              </button>

              {/* Fullscreen Toggle */}
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors"
                title="Toggle Fullscreen"
                aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
                aria-pressed={isFullscreen}
              >
                {isFullscreen ? (
                  <Minimize2 size={20} className="text-neutral-700 dark:text-neutral-300" />
                ) : (
                  <Maximize2 size={20} className="text-neutral-700 dark:text-neutral-300" />
                )}
              </button>

              {/* Close Button */}
              <button
                ref={closeButtonRef}
                onClick={onClose}
                className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors"
                title="Close (Esc)"
                aria-label="Close PDF viewer"
              >
                <X size={20} className="text-neutral-700 dark:text-neutral-300" />
              </button>
            </div>
          </div>
        </div>

        {/* PDF Content */}
        <div className="h-full pt-20 pb-20 overflow-auto bg-neutral-50 dark:bg-neutral-950" role="main" aria-label="PDF content">
          <div className="flex items-center justify-center min-h-full p-8">
            {isLoading ? (
              <div className="text-center" role="status" aria-live="polite">
                <div className="inline-block w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mb-4" aria-hidden="true" />
                <p className="text-neutral-600 dark:text-neutral-400">Loading PDF...</p>
              </div>
            ) : (
              <div className="relative">
                <canvas
                  ref={canvasRef}
                  className="shadow-2xl rounded-lg bg-white"
                  role="img"
                  aria-label={`Page ${currentPage} of ${fileName}`}
                />
                {/* Text Layer for highlighting */}
                <div
                  ref={textLayerRef}
                  className="absolute top-0 left-0 pointer-events-none"
                  aria-hidden="true"
                />
                {/* Highlight Overlays - Multiple boxes for multi-line text */}
                {highlightPositions.map((position, index) => (
                  <div
                    key={index}
                    className="absolute bg-yellow-400/40 border-2 border-yellow-500 rounded animate-pulse-highlight pointer-events-none"
                    style={{
                      left: `${position.x}px`,
                      top: `${position.y}px`,
                      width: `${position.width}px`,
                      height: `${position.height}px`,
                    }}
                    role="mark"
                    aria-label={index === 0 ? "Highlighted text" : undefined}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="absolute bottom-0 left-0 right-0 z-10 bg-gradient-to-t from-white/95 dark:from-neutral-900/95 to-transparent backdrop-blur-md border-t border-neutral-200 dark:border-neutral-800">
          <div className="flex items-center justify-center gap-4 p-4" role="navigation" aria-label="PDF page navigation">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Previous Page (←)"
              aria-label="Previous page"
            >
              <ChevronLeft size={20} className="text-neutral-700 dark:text-neutral-300" />
            </button>

            <div className="flex items-center gap-2">
              <input
                type="number"
                value={currentPage}
                onChange={(e) => {
                  const page = parseInt(e.target.value);
                  if (page >= 1 && page <= totalPages) setCurrentPage(page);
                }}
                className="w-16 px-2 py-1 text-center bg-neutral-100 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-lg text-neutral-900 dark:text-neutral-100"
                min={1}
                max={totalPages}
                aria-label="Current page number"
                aria-describedby="pdf-viewer-description"
              />
              <span className="text-neutral-500 dark:text-neutral-400" aria-hidden="true">/ {totalPages}</span>
            </div>

            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Next page"
              title="Next Page (→)">
              <ChevronRight size={20} className="text-neutral-700 dark:text-neutral-300" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
