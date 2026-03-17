import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Scan,
  HardHat,
  PackageCheck,
  AlertTriangle,
  FileText,
  Users,
  Bell,
  LogOut,
  Shield,
  UserCircle,
  ChevronDown,
  BookOpen,
  Grid3X3,
  Settings,
  Menu,
  X,
  ClipboardList
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '../components/ui/sheet';
import EcosystemSwitcher from './EcosystemSwitcher';

const NavItems = ({ items, onItemClick }) => {
  return items.map((item) => (
    <NavLink
      key={item.to}
      to={item.to}
      onClick={onItemClick}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
          isActive
            ? 'bg-blue-500 text-white'
            : 'text-slate-600 hover:bg-slate-100'
        }`
      }
      data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <item.icon className="w-5 h-5 flex-shrink-0" />
      <span className="font-medium">{item.label}</span>
    </NavLink>
  ));
};

const SidebarContent = ({ user, handleLogout, onItemClick }) => {
  const operationItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/scan360', icon: Scan, label: 'Scan 360°' },
    { to: '/incidents', icon: AlertTriangle, label: 'Incidentes' },
    { to: '/findings', icon: FileText, label: 'Hallazgos' },
  ];

  const managementItems = [
    { to: '/epp', icon: HardHat, label: 'Gestión EPP' },
    { to: '/epp/entregas', icon: PackageCheck, label: 'Entregas EPP' },
    { to: '/procedures', icon: BookOpen, label: 'Procedimientos' },
    { to: '/risk-matrix', icon: Grid3X3, label: 'Matriz de Riesgos' },
    { to: '/forms', icon: ClipboardList, label: 'Formularios' },
  ];

  const adminItems = [
    { to: '/profiles', icon: UserCircle, label: 'Perfiles' },
    { to: '/users', icon: Users, label: 'Usuarios' },
    { to: '/config', icon: Settings, label: 'Configuracion' },
  ];

  return (
    <>
      {/* Ecosystem Switcher */}
      <div className="border-b border-slate-200">
        <EcosystemSwitcher />
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 lg:p-4 space-y-1 overflow-y-auto">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 mb-3">
          Operación
        </p>
        <NavItems items={operationItems} onItemClick={onItemClick} />

        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 mt-6 mb-3">
          Habilitación
        </p>
        <NavItems items={managementItems} onItemClick={onItemClick} />

        {(user?.role === 'admin' || user?.role === 'superadmin') && (
          <>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 mt-6 mb-3">
              Administración
            </p>
            <NavItems items={adminItems} onItemClick={onItemClick} />
          </>
        )}
      </nav>

      {/* User Info */}
      <div className="p-3 lg:p-4 border-t border-slate-200">
        <div className="flex items-center gap-3 mb-3 lg:mb-4">
          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-white font-semibold text-sm">
              {user?.name?.charAt(0)?.toUpperCase() || 'A'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-900 truncate">{user?.name || 'Administrador'}</p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
        </div>
        <Button
          variant="outline"
          className="w-full justify-start gap-2 rounded-lg text-sm"
          onClick={handleLogout}
          data-testid="logout-btn"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Cerrar Sesión</span>
          <span className="sm:hidden">Salir</span>
        </Button>
      </div>
    </>
  );
};

export const Sidebar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const closeMobile = () => setMobileOpen(false);

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-64 bg-white border-r border-slate-200 flex-col h-screen sticky top-0" data-testid="sidebar">
        <SidebarContent user={user} handleLogout={handleLogout} />
      </aside>

      {/* Mobile Sidebar (Sheet) */}
      <div className="lg:hidden fixed top-0 left-0 z-50 p-4">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon" className="bg-white shadow-md" data-testid="mobile-menu-btn">
              <Menu className="w-5 h-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72 p-0">
            <div className="flex flex-col h-full">
              <SidebarContent user={user} handleLogout={handleLogout} onItemClick={closeMobile} />
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
};

export const TopBar = ({ title, subtitle, children }) => {
  return (
    <header className="bg-white border-b border-slate-200 px-4 lg:px-8 py-3 lg:py-4 flex items-center justify-between sticky top-0 z-10" data-testid="topbar">
      <div className="ml-12 lg:ml-0">
        <h1 className="text-lg sm:text-xl lg:text-2xl font-bold text-slate-900 truncate">{title}</h1>
        {subtitle && <p className="text-xs sm:text-sm text-slate-500 mt-0.5 lg:mt-1 truncate hidden sm:block">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-2 lg:gap-4 flex-shrink-0">
        {children}
      </div>
    </header>
  );
};
