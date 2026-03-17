import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Calendar, 
  ClipboardList, 
  ChevronDown, 
  ExternalLink,
  Check,
  Lock
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { Badge } from '../components/ui/badge';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const APP_ICONS = {
  shield: Shield,
  calendar: Calendar,
  clipboard: ClipboardList
};

const APP_COLORS = {
  smartsafety: 'bg-blue-500',
  smartplan: 'bg-purple-500',
  smartforms: 'bg-green-500'
};

export default function EcosystemSwitcher() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApps();
  }, []);

  const fetchApps = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/ecosystem/apps`);
      setApps(response.data);
    } catch (error) {
      // Use default apps if API fails
      setApps([
        {
          id: "smartsafety",
          name: "SmartSafety+",
          code: "smartsafety",
          description: "Gestión de seguridad",
          icon: "shield",
          is_active: true,
          is_current: true
        },
        {
          id: "smartplan",
          name: "SmartPlan+",
          code: "smartplan",
          description: "Planificación de tareas",
          icon: "calendar",
          is_active: false,
          is_current: false
        },
        {
          id: "smartforms",
          name: "SmartForms+",
          code: "smartforms",
          description: "Formularios dinámicos",
          icon: "clipboard",
          is_active: false,
          is_current: false
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const currentApp = apps.find(app => app.is_current) || apps[0];
  const CurrentIcon = currentApp ? APP_ICONS[currentApp.icon] || Shield : Shield;

  const handleAppSwitch = (app) => {
    if (!app.is_active || app.is_current) return;
    
    if (app.url) {
      window.location.href = app.url;
    }
  };

  if (loading || !currentApp) {
    return (
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="w-10 h-10 bg-blue-500 rounded-xl animate-pulse"></div>
        <div className="h-4 bg-slate-200 rounded w-24 animate-pulse"></div>
      </div>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button 
          className="flex items-center gap-3 px-4 py-3 w-full hover:bg-slate-50 transition-colors rounded-lg"
          data-testid="ecosystem-switcher"
        >
          <div className={`w-10 h-10 ${APP_COLORS[currentApp.code] || 'bg-blue-500'} rounded-xl flex items-center justify-center flex-shrink-0`}>
            <CurrentIcon className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1 text-left min-w-0">
            <div className="font-bold text-sm truncate">
              <span className="text-blue-600">Smart</span>
              <span className="text-orange-500">{currentApp.name.replace('Smart', '')}</span>
            </div>
            <div className="text-xs text-slate-500">Enterprise 2026</div>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" />
        </button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="start" className="w-64">
        <DropdownMenuLabel className="text-xs text-slate-500 font-normal">
          Ecosistema Smart+
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        {apps.map((app) => {
          const Icon = APP_ICONS[app.icon] || Shield;
          const isDisabled = !app.is_active || !app.url;
          
          return (
            <DropdownMenuItem
              key={app.id}
              className={`flex items-center gap-3 p-3 cursor-pointer ${
                isDisabled && !app.is_current ? 'opacity-50' : ''
              }`}
              onClick={() => handleAppSwitch(app)}
              disabled={isDisabled && !app.is_current}
            >
              <div className={`w-9 h-9 ${APP_COLORS[app.code] || 'bg-slate-500'} rounded-lg flex items-center justify-center`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm flex items-center gap-2">
                  {app.name}
                  {app.is_current && (
                    <Check className="w-4 h-4 text-green-500" />
                  )}
                </div>
                <div className="text-xs text-slate-500 truncate">{app.description}</div>
              </div>
              {!app.is_active && !app.is_current && (
                <Badge variant="outline" className="text-xs gap-1">
                  <Lock className="w-3 h-3" />
                  No activo
                </Badge>
              )}
              {app.is_active && app.url && !app.is_current && (
                <ExternalLink className="w-4 h-4 text-slate-400" />
              )}
            </DropdownMenuItem>
          );
        })}
        
        <DropdownMenuSeparator />
        <div className="px-3 py-2 text-xs text-slate-400">
          Contacta a tu administrador para activar más aplicaciones
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
