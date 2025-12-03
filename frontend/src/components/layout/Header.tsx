'use client';

import React from 'react';
import { Bell, Moon, Sun, User, Menu } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';
import { Button } from '@/components/ui/Button';

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="h-16 border-b border-[#455A64] flex items-center justify-between px-4 lg:px-6 shadow-sm" style={{ background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)' }}>
      <div className="flex items-center gap-4">
        {/* Hamburger Menu - only visible on mobile/tablet */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onMenuClick}
          className="lg:hidden text-white/80 hover:text-white hover:bg-white/10"
        >
          <Menu size={24} />
        </Button>
        <h2 className="text-lg font-normal text-white">Dynamic Pricing Intelligence</h2>
      </div>

      <div className="flex items-center gap-2">
        {/* Notifications */}
        <Button variant="ghost" size="icon" className="text-white/80 hover:text-white hover:bg-white/10">
          <Bell size={20} />
        </Button>

        {/* Theme Toggle */}
        <Button variant="ghost" size="icon" onClick={toggleTheme} className="text-white/80 hover:text-white hover:bg-white/10">
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </Button>

        {/* User Profile */}
        <Button variant="ghost" size="icon" className="text-white/80 hover:text-white hover:bg-white/10">
          <User size={20} />
        </Button>
      </div>
    </header>
  );
}

