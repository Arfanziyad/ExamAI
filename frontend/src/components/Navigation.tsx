
import { Link, useLocation } from 'react-router-dom';
import { Home, Plus, BookOpen, Settings, BarChart3, Zap } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/create', label: 'Create Test', icon: Plus },
    { path: '/submit-multi', label: 'Smart Submit', icon: Zap },
    { path: '/take', label: 'Take Test', icon: BookOpen },
    { path: '/evaluate', label: 'Evaluate', icon: Settings },
    { path: '/results', label: 'View Results', icon: BarChart3 },
    { path: '/results-aggregated', label: 'Analytics', icon: BarChart3 }
  ];

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-center space-x-8">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center space-x-2 px-4 py-4 text-sm font-medium border-b-2 transition-colors duration-200 ${
                location.pathname === path
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;