import React from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hoverable?: boolean;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  footer?: React.ReactNode;
  onClick?: () => void;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  hoverable = true,
  title,
  subtitle,
  footer,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`
        glass-panel 
        rounded-xl 
        p-6 
        shadow-card-shadow 
        flex 
        flex-col
        ${hoverable ? 'glass-panel-hover cursor-pointer' : ''} 
        ${onClick ? 'cursor-pointer active:scale-[0.98]' : ''} 
        ${className}
      `}
    >
      {(title || subtitle) && (
        <div className="mb-4">
          {title && <h3 className="text-lg font-bold text-zinc-100 leading-tight">{title}</h3>}
          {subtitle && <p className="text-xs text-zinc-400 mt-1 leading-normal">{subtitle}</p>}
        </div>
      )}
      
      <div className="flex-1 text-sm text-zinc-300 leading-relaxed">
        {children}
      </div>

      {footer && (
        <div className="mt-4 pt-4 border-t border-amber-500/10 flex items-center justify-end text-xs text-zinc-400 leading-normal">
          {footer}
        </div>
      )}
    </div>
  );
};

export default GlassCard;
