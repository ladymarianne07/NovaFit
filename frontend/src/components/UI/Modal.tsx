/**
 * Modal Component - Cartoon Style Modal Dialog
 * Following NovaFitness design guidelines
 */
import React, { useEffect } from 'react';
import './Modal.css';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showCloseButton?: boolean;
  confirmText?: string;
  cancelText?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
  confirmText,
  cancelText,
  onConfirm,
  onCancel,
  variant = 'default',
}) => {
  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div 
        className="absolute inset-0 bg-[var(--color-bg-modal-overlay)] backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className={`
        relative bg-[var(--color-bg-card)] rounded-[var(--rounded-modal)] 
        shadow-[var(--shadow-dialog)] max-h-[90vh] overflow-auto
        animate-slide-in-up ${sizeClasses[size]} w-full
      `}>
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-6 border-b border-[var(--color-border-divider)]">
            {title && (
              <h3 className="text-lg font-semibold text-[var(--color-text-default)]">
                {title}
              </h3>
            )}
            {showCloseButton && (
              <button
                onClick={onClose}
                className="text-[var(--color-text-muted)] hover:text-[var(--color-text-default)] transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        )}
        
        {/* Content */}
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );

  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm();
    }
    onClose();
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
    onClose();
  };

  return (
    <div className="nova-modal-backdrop" onClick={handleBackdropClick}>
      <div className={`nova-modal nova-modal--${size} nova-modal--${variant}`}>
        {/* Modal Header */}
        {(title || showCloseButton) && (
          <div className="nova-modal__header">
            {title && <h2 className="nova-modal__title">{title}</h2>}
            {showCloseButton && (
              <button className="nova-modal__close" onClick={onClose}>
                ×
              </button>
            )}
          </div>
        )}

        {/* Modal Body */}
        <div className="nova-modal__body">
          {children}
        </div>

        {/* Modal Footer */}
        {(confirmText || cancelText) && (
          <div className="nova-modal__footer">
            {cancelText && (
              <button
                className="nova-button nova-button--secondary"
                onClick={handleCancel}
              >
                {cancelText}
              </button>
            )}
            {confirmText && (
              <button
                className={`nova-button nova-button--${variant === 'danger' ? 'danger' : 'primary'}`}
                onClick={handleConfirm}
              >
                {confirmText}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Modal;