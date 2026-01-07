
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Brain, HelpCircle } from 'lucide-react';
import Navigation from './components/Navigation';
import Home from './pages/Home';
import CreateTest from './pages/CreateTest';
import TakeTest from './pages/TakeTest';
import SubmitMultiAnswer from './pages/SubmitMultiAnswer';
import EvaluatePage from './pages/EvaluatePage';
import ViewResults from './pages/ViewResults';
import ViewAggregatedResults from './pages/ViewAggregatedResults';
import './index.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
        {/* Header */}
        <header className="bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-3">
                <div className="bg-white bg-opacity-20 p-2 rounded-lg">
                  <Brain className="h-6 w-6" />
                </div>
                <h1 className="text-xl font-semibold tracking-tight">AI Exam Evaluator</h1>
              </div>
              <button className="flex items-center space-x-2 bg-white bg-opacity-10 hover:bg-opacity-20 px-4 py-2 rounded-lg transition-colors duration-200">
                <HelpCircle className="h-4 w-4" />
                <span className="text-sm font-medium">Help</span>
              </button>
            </div>
          </div>
        </header>

        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/create" element={<CreateTest />} />
            <Route path="/take" element={<TakeTest />} />
            <Route path="/submit-multi" element={<SubmitMultiAnswer />} />
            <Route path="/evaluate" element={<EvaluatePage />} />
            <Route path="/results" element={<ViewResults />} />
            <Route path="/results-aggregated" element={<ViewAggregatedResults />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;