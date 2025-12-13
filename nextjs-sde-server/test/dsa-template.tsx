import React, { useState, useEffect, useRef } from 'react';
import { Save, Clock, Search, Download, Upload, Trash2, Plus, Edit, CheckSquare, Square, Menu, X, BarChart3, Code, FileText, Copy, Check } from 'lucide-react';

const DSAMasteryTracker = () => {
  const [problems, setProblems] = useState([]);
  const [currentProblem, setCurrentProblem] = useState(null);
  const [view, setView] = useState('form'); // form, list, stats
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [timer, setTimer] = useState(0);
  const [timerRunning, setTimerRunning] = useState(false);
  const [copied, setCopied] = useState(false);
  const timerRef = useRef(null);

  // Load problems from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('dsa_problems');
    if (saved) {
      setProblems(JSON.parse(saved));
    }
  }, []);

  // Save problems to localStorage
  useEffect(() => {
    if (problems.length > 0) {
      localStorage.setItem('dsa_problems', JSON.stringify(problems));
    }
  }, [problems]);

  // Timer effect
  useEffect(() => {
    if (timerRunning) {
      timerRef.current = setInterval(() => {
        setTimer(prev => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [timerRunning]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const initNewProblem = () => {
    const template = {
      id: Date.now(),
      createdAt: new Date().toISOString(),
      problemName: '',
      difficulty: '',
      timeSpent: 0,
      pattern: '',
      category: '',
      leetcodeUrl: '',
      problemDescription: '',
      input: '',
      output: '',
      constraints: '',
      timeComplexityTarget: '',
      spaceComplexityTarget: '',
      example1Input: '',
      example1Output: '',
      example1Why: '',
      example2Input: '',
      example2Output: '',
      example2Why: '',
      edgeCases: {
        emptyInput: false,
        singleElement: false,
        allSame: false,
        maxSize: false,
        negative: false,
        duplicates: false,
        sorted: false,
        reverseSorted: false,
        custom1: '',
        custom2: ''
      },
      patterns: {
        array: false,
        twoPointers: false,
        slidingWindow: false,
        binarySearch: false,
        hashMap: false,
        stack: false,
        heap: false,
        linkedList: false,
        tree: false,
        graph: false,
        backtracking: false,
        dp: false,
        greedy: false,
        divideConquer: false,
        bitManipulation: false,
        math: false
      },
      selectedPattern: '',
      similarProblems: '',
      bruteForce: { idea: '', time: '', space: '', whySlow: '' },
      optimization1: { idea: '', time: '', space: '', tradeoff: '' },
      optimization2: { idea: '', time: '', space: '', whyWorks: '' },
      selectedApproach: '',
      algorithmSteps: ['', '', '', ''],
      invariants: ['', ''],
      pseudocode: '',
      language: 'rust',
      code: '',
      timeBest: '',
      timeAverage: '',
      timeWorst: '',
      space: '',
      learnings: '',
      mistakes: '',
      keyInsight: '',
      completed: false
    };
    setCurrentProblem(template);
    setTimer(0);
    setTimerRunning(true);
    setView('form');
  };

  const saveProblem = () => {
    if (!currentProblem.problemName) {
      alert('Please enter a problem name');
      return;
    }
    
    const updatedProblem = { ...currentProblem, timeSpent: timer };
    
    const existingIndex = problems.findIndex(p => p.id === currentProblem.id);
    if (existingIndex >= 0) {
      const updated = [...problems];
      updated[existingIndex] = updatedProblem;
      setProblems(updated);
    } else {
      setProblems([updatedProblem, ...problems]);
    }
    
    setTimerRunning(false);
    alert('Problem saved successfully!');
  };

  const loadProblem = (problem) => {
    setCurrentProblem(problem);
    setTimer(problem.timeSpent || 0);
    setTimerRunning(false);
    setView('form');
  };

  const deleteProblem = (id) => {
    if (confirm('Are you sure you want to delete this problem?')) {
      setProblems(problems.filter(p => p.id !== id));
      if (currentProblem?.id === id) {
        setCurrentProblem(null);
      }
    }
  };

  const exportData = () => {
    const dataStr = JSON.stringify(problems, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `dsa-problems-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
  };

  const importData = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target.result);
          setProblems(imported);
          alert('Data imported successfully!');
        } catch (error) {
          alert('Error importing data. Please check the file format.');
        }
      };
      reader.readAsText(file);
    }
  };

  const copyToClipboard = () => {
    const text = generateMarkdown(currentProblem);
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const generateMarkdown = (problem) => {
    return `# ${problem.problemName}
**Difficulty:** ${problem.difficulty} | **Time:** ${formatTime(problem.timeSpent)}
**Pattern:** ${problem.pattern} | **Category:** ${problem.category}

## Problem Description
${problem.problemDescription}

## Approach
${problem.selectedApproach}

## Code (${problem.language})
\`\`\`${problem.language}
${problem.code}
\`\`\`

## Complexity
- Time: ${problem.timeWorst}
- Space: ${problem.space}

## Key Insight
${problem.keyInsight}`;
  };

  const filteredProblems = problems.filter(p => 
    p.problemName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.pattern.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const stats = {
    total: problems.length,
    completed: problems.filter(p => p.completed).length,
    avgTime: problems.length > 0 ? Math.round(problems.reduce((acc, p) => acc + p.timeSpent, 0) / problems.length) : 0,
    byDifficulty: {
      easy: problems.filter(p => p.difficulty === 'Easy').length,
      medium: problems.filter(p => p.difficulty === 'Medium').length,
      hard: problems.filter(p => p.difficulty === 'Hard').length
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-gray-100 flex">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden bg-gray-900/50 backdrop-blur-sm border-r border-gray-700/50`}>
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              Problems
            </h2>
            <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-gray-400 hover:text-white">
              <X size={20} />
            </button>
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" size={18} />
            <input
              type="text"
              placeholder="Search problems..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
            />
          </div>

          <div className="space-y-2 max-h-[calc(100vh-250px)] overflow-y-auto custom-scrollbar">
            {filteredProblems.map(problem => (
              <div
                key={problem.id}
                className="group p-3 bg-gray-800/30 hover:bg-gray-800/60 border border-gray-700/50 rounded-lg cursor-pointer transition-all duration-200 hover:scale-[1.02]"
                onClick={() => loadProblem(problem)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {problem.completed ? (
                        <CheckSquare size={16} className="text-green-400 flex-shrink-0" />
                      ) : (
                        <Square size={16} className="text-gray-500 flex-shrink-0" />
                      )}
                      <h3 className="font-semibold text-sm truncate">{problem.problemName || 'Untitled'}</h3>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <span className={`px-2 py-0.5 rounded ${
                        problem.difficulty === 'Easy' ? 'bg-green-500/20 text-green-400' :
                        problem.difficulty === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {problem.difficulty}
                      </span>
                      <span>{formatTime(problem.timeSpent)}</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteProblem(problem.id); }}
                    className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 transition-opacity"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <button
              onClick={exportData}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg transition-all text-sm"
            >
              <Download size={16} />
              Export
            </button>
            <label className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg transition-all cursor-pointer text-sm">
              <Upload size={16} />
              Import
              <input type="file" accept=".json" onChange={importData} className="hidden" />
            </label>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-700/50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {!sidebarOpen && (
                <button onClick={() => setSidebarOpen(true)} className="text-gray-400 hover:text-white">
                  <Menu size={24} />
                </button>
              )}
              <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400">
                DSA Mastery Tracker
              </h1>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg">
                <Clock size={18} className="text-blue-400" />
                <span className="font-mono text-lg">{formatTime(timer)}</span>
                <button
                  onClick={() => setTimerRunning(!timerRunning)}
                  className={`ml-2 px-3 py-1 rounded ${
                    timerRunning ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                  } transition-all text-sm`}
                >
                  {timerRunning ? 'Pause' : 'Start'}
                </button>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setView('stats')}
                  className={`p-2 rounded-lg transition-all ${
                    view === 'stats' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  <BarChart3 size={20} />
                </button>
                <button
                  onClick={initNewProblem}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 rounded-lg transition-all font-semibold"
                >
                  <Plus size={20} />
                  New Problem
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
          {view === 'stats' ? (
            <StatsView stats={stats} problems={problems} />
          ) : currentProblem ? (
            <ProblemForm
              problem={currentProblem}
              setProblem={setCurrentProblem}
              onSave={saveProblem}
              onCopy={copyToClipboard}
              copied={copied}
            />
          ) : (
            <EmptyState onNewProblem={initNewProblem} />
          )}
        </div>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(31, 41, 55, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(75, 85, 99, 0.5);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(107, 114, 128, 0.7);
        }
      `}</style>
    </div>
  );
};

const StatsView = ({ stats, problems }) => (
  <div className="max-w-6xl mx-auto space-y-6">
    <h2 className="text-3xl font-bold mb-6">Your Progress</h2>
    
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <StatCard title="Total Problems" value={stats.total} color="blue" />
      <StatCard title="Completed" value={stats.completed} color="green" />
      <StatCard title="Avg Time" value={`${Math.floor(stats.avgTime / 60)}m`} color="purple" />
      <StatCard title="This Week" value={problems.filter(p => {
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        return new Date(p.createdAt) > weekAgo;
      }).length} color="pink" />
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-4">By Difficulty</h3>
        <div className="space-y-3">
          <DifficultyBar label="Easy" count={stats.byDifficulty.easy} total={stats.total} color="green" />
          <DifficultyBar label="Medium" count={stats.byDifficulty.medium} total={stats.total} color="yellow" />
          <DifficultyBar label="Hard" count={stats.byDifficulty.hard} total={stats.total} color="red" />
        </div>
      </div>

      <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-4">Recent Activity</h3>
        <div className="space-y-2">
          {problems.slice(0, 5).map(p => (
            <div key={p.id} className="flex justify-between items-center text-sm">
              <span className="truncate flex-1">{p.problemName || 'Untitled'}</span>
              <span className="text-gray-400 ml-2">{new Date(p.createdAt).toLocaleDateString()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

const StatCard = ({ title, value, color }) => {
  const colors = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
    pink: 'from-pink-500 to-pink-600'
  };

  return (
    <div className={`bg-gradient-to-br ${colors[color]} rounded-xl p-6 shadow-lg`}>
      <div className="text-white/80 text-sm mb-2">{title}</div>
      <div className="text-3xl font-bold text-white">{value}</div>
    </div>
  );
};

const DifficultyBar = ({ label, count, total, color }) => {
  const percentage = total > 0 ? (count / total) * 100 : 0;
  const colors = {
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500'
  };

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span>{label}</span>
        <span className="text-gray-400">{count}</span>
      </div>
      <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${colors[color]} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

const EmptyState = ({ onNewProblem }) => (
  <div className="flex items-center justify-center h-full">
    <div className="text-center space-y-4">
      <Code size={64} className="mx-auto text-gray-600" />
      <h3 className="text-2xl font-semibold text-gray-400">No Problem Selected</h3>
      <p className="text-gray-500">Start your journey to the top 1%</p>
      <button
        onClick={onNewProblem}
        className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 rounded-lg transition-all font-semibold"
      >
        Create Your First Problem
      </button>
    </div>
  </div>
);

const ProblemForm = ({ problem, setProblem, onSave, onCopy, copied }) => {
  const update = (field, value) => {
    setProblem({ ...problem, [field]: value });
  };

  const updateNested = (parent, field, value) => {
    setProblem({
      ...problem,
      [parent]: { ...problem[parent], [field]: value }
    });
  };

  const updateArray = (field, index, value) => {
    const arr = [...problem[field]];
    arr[index] = value;
    setProblem({ ...problem, [field]: arr });
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header Actions */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Problem Workspace</h2>
        <div className="flex gap-2">
          <button
            onClick={onCopy}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg transition-all"
          >
            {copied ? <Check size={18} className="text-green-400" /> : <Copy size={18} />}
            {copied ? 'Copied!' : 'Copy Markdown'}
          </button>
          <button
            onClick={onSave}
            className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-lg transition-all font-semibold"
          >
            <Save size={18} />
            Save Problem
          </button>
        </div>
      </div>

      {/* Section 0: LeetCode Import */}
      <Section title="LeetCode Problem" icon={<FileText size={20} />}>
        <div className="space-y-4">
          <Input
            label="LeetCode URL"
            value={problem.leetcodeUrl}
            onChange={(e) => update('leetcodeUrl', e.target.value)}
            placeholder="https://leetcode.com/problems/..."
          />
          <TextArea
            label="Paste Problem Description"
            value={problem.problemDescription}
            onChange={(e) => update('problemDescription', e.target.value)}
            rows={6}
            placeholder="Paste the full problem description from LeetCode here..."
          />
        </div>
      </Section>

      {/* Section 1: Problem Header */}
      <Section title="1. Problem Header" icon={<Edit size={20} />}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Problem Name"
            value={problem.problemName}
            onChange={(e) => update('problemName', e.target.value)}
            placeholder="e.g., Two Sum"
            required
          />
          <Select
            label="Difficulty"
            value={problem.difficulty}
            onChange={(e) => update('difficulty', e.target.value)}
            options={['', 'Easy', 'Medium', 'Hard']}
          />
          <Input
            label="Pattern"
            value={problem.pattern}
            onChange={(e) => update('pattern', e.target.value)}
            placeholder="e.g., Hash Map"
          />
          <Input
            label="Category"
            value={problem.category}
            onChange={(e) => update('category', e.target.value)}
            placeholder="e.g., Array, String"
          />
        </div>
      </Section>

      {/* Section 2: Understand & Visualize */}
      <Section title="2. Understand & Visualize">
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Input Format"
              value={problem.input}
              onChange={(e) => update('input', e.target.value)}
              placeholder="e.g., Array of integers"
            />
            <Input
              label="Output Format"
              value={problem.output}
              onChange={(e) => update('output', e.target.value)}
              placeholder="e.g., Single integer"
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Constraints"
              value={problem.constraints}
              onChange={(e) => update('constraints', e.target.value)}
              placeholder="n ≤ 10^5"
            />
            <Input
              label="Target Time"
              value={problem.timeComplexityTarget}
              onChange={(e) => update('timeComplexityTarget', e.target.value)}
              placeholder="O(n)"
            />
            <Input
              label="Target Space"
              value={problem.spaceComplexityTarget}
              onChange={(e) => update('spaceComplexityTarget', e.target.value)}
              placeholder="O(1)"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-300">Example 1 (Given)</label>
              <Input
                label="Input"
                value={problem.example1Input}
                onChange={(e) => update('example1Input', e.target.value)}
                placeholder="[2,7,11,15], 9"
              />
              <Input
                label="Output"
                value={problem.example1Output}
                onChange={(e) => update('example1Output', e.target.value)}
                placeholder="[0,1]"
              />
              <Input
                label="Why?"
                value={problem.example1Why}
                onChange={(e) => update('example1Why', e.target.value)}
                placeholder="nums[0] + nums[1] == 9"
              />
            </div>
            
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-300">Example 2 (Your Own)</label>
              <Input
                label="Input"
                value={problem.example2Input}
                onChange={(e) => update('example2Input', e.target.value)}
                placeholder="Create your own test case"
              />
              <Input
                label="Output"
                value={problem.example2Output}
                onChange={(e) => update('example2Output', e.target.value)}
                placeholder="Expected output"
              />
              <Input
                label="Why?"
                value={problem.example2Why}
                onChange={(e) => update('example2Why', e.target.value)}
                placeholder="Explanation"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-3">Edge Cases</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(problem.edgeCases).map(([key, value]) => {
                if (key.startsWith('custom')) {
                  return (
                    <Input
                      key={key}
                      placeholder={key === 'custom1' ? 'Custom edge case 1' : 'Custom edge case 2'}
                      value={value}
                      onChange={(e) => updateNested('edgeCases', key, e.target.value)}
                    />
                  );
                }
                return (
                  <Checkbox
                    key={key}
                    label={key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                    checked={value}
                    onChange={(e) => updateNested('edgeCases', key, e.target.checked)}
                  />
                );
              })}
            </div>
          </div>
        </div>
      </Section>

      {/* Section 3: Pattern Recognition */}
      <Section title="3. Pattern Recognition">
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(problem.patterns).map(([key, value]) => (
              <Checkbox
                key={key}
                label={key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                checked={value}
                onChange={(e) => updateNested('patterns', key, e.target.checked)}
              />
            ))}
          </div>
          <Input
            label="Selected Pattern"
            value={problem.selectedPattern}
            onChange={(e) => update('selectedPattern', e.target.value)}
            placeholder="Primary pattern for this problem"
          />
          <Input
            label="Similar Problems Solved"
            value={problem.similarProblems}
            onChange={(e) => update('similarProblems', e.target.value)}
            placeholder="List similar problems you've solved"
          />
        </div>
      </Section>

      {/* Section 4: Approach Comparison */}
      <Section title="4. Approach Comparison">
        <div className="space-y-6">
          <ApproachBox
            title="Brute Force"
            approach={problem.bruteForce}
            onChange={(field, value) => updateNested('bruteForce', field, value)}
            fields={['idea', 'time', 'space', 'whySlow']}
            labels={['Idea', 'Time', 'Space', 'Why Too Slow']}
          />
          <ApproachBox
            title="Optimization 1"
            approach={problem.optimization1}
            onChange={(field, value) => updateNested('optimization1', field, value)}
            fields={['idea', 'time', 'space', 'tradeoff']}
            labels={['Idea', 'Time', 'Space', 'Trade-off']}
          />
          <ApproachBox
            title="Optimization 2 (Target)"
            approach={problem.optimization2}
            onChange={(field, value) => updateNested('optimization2', field, value)}
            fields={['idea', 'time', 'space', 'whyWorks']}
            labels={['Idea', 'Time', 'Space', 'Why This Works']}
          />
          <Input
            label="Selected Approach"
            value={problem.selectedApproach}
            onChange={(e) => update('selectedApproach', e.target.value)}
            placeholder="Which approach will you implement?"
          />
        </div>
      </Section>

      {/* Section 5: Algorithm Plan */}
      <Section title="5. Detailed Algorithm Plan">
        <div className="space-y-4">
          {problem.algorithmSteps.map((step, idx) => (
            <TextArea
              key={idx}
              label={`Step ${idx + 1}`}
              value={step}
              onChange={(e) => updateArray('algorithmSteps', idx, e.target.value)}
              rows={2}
              placeholder={`Describe step ${idx + 1}...`}
            />
          ))}
          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-2">Invariants</label>
            {problem.invariants.map((inv, idx) => (
              <Input
                key={idx}
                value={inv}
                onChange={(e) => updateArray('invariants', idx, e.target.value)}
                placeholder={`Invariant ${idx + 1}: What's ALWAYS true in your loop?`}
                className="mb-2"
              />
            ))}
          </div>
        </div>
      </Section>

      {/* Section 6: Code */}
      <Section title="6. Code Implementation">
        <div className="space-y-4">
          <Select
            label="Programming Language"
            value={problem.language}
            onChange={(e) => update('language', e.target.value)}
            options={['rust', 'python', 'go', 'javascript', 'cpp', 'java']}
          />
          <TextArea
            label="Pseudocode / Plan"
            value={problem.pseudocode}
            onChange={(e) => update('pseudocode', e.target.value)}
            rows={6}
            placeholder="Write your pseudocode here..."
            mono
          />
          <TextArea
            label="Implementation"
            value={problem.code}
            onChange={(e) => update('code', e.target.value)}
            rows={15}
            placeholder="Write your code here..."
            mono
          />
        </div>
      </Section>

      {/* Section 7: Complexity Analysis */}
      <Section title="7. Complexity Analysis">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Time - Best Case"
            value={problem.timeBest}
            onChange={(e) => update('timeBest', e.target.value)}
            placeholder="O(?)"
          />
          <Input
            label="Time - Average Case"
            value={problem.timeAverage}
            onChange={(e) => update('timeAverage', e.target.value)}
            placeholder="O(?)"
          />
          <Input
            label="Time - Worst Case"
            value={problem.timeWorst}
            onChange={(e) => update('timeWorst', e.target.value)}
            placeholder="O(?)"
          />
          <Input
            label="Space Complexity"
            value={problem.space}
            onChange={(e) => update('space', e.target.value)}
            placeholder="O(?)"
          />
        </div>
      </Section>

      {/* Section 8: Reflection */}
      <Section title="8. Post-Solve Reflection">
        <div className="space-y-4">
          <TextArea
            label="What I Learned"
            value={problem.learnings}
            onChange={(e) => update('learnings', e.target.value)}
            rows={3}
            placeholder="Key takeaways from this problem..."
          />
          <TextArea
            label="Mistakes Made"
            value={problem.mistakes}
            onChange={(e) => update('mistakes', e.target.value)}
            rows={3}
            placeholder="What went wrong? What would you do differently?"
          />
          <TextArea
            label="Key Insight to Remember"
            value={problem.keyInsight}
            onChange={(e) => update('keyInsight', e.target.value)}
            rows={2}
            placeholder="The one thing you'll remember from this problem..."
          />
          <Checkbox
            label="Mark as Completed"
            checked={problem.completed}
            onChange={(e) => update('completed', e.target.checked)}
          />
        </div>
      </Section>
    </div>
  );
};

const Section = ({ title, icon, children }) => (
  <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-6 hover:border-gray-600/50 transition-all">
    <div className="flex items-center gap-3 mb-6">
      {icon && <div className="text-blue-400">{icon}</div>}
      <h3 className="text-xl font-bold text-gray-200">{title}</h3>
    </div>
    {children}
  </div>
);

const Input = ({ label, className = '', mono = false, ...props }) => (
  <div className={className}>
    {label && <label className="block text-sm font-semibold text-gray-300 mb-2">{label}</label>}
    <input
      className={`w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all text-gray-100 placeholder-gray-500 ${mono ? 'font-mono text-sm' : ''}`}
      {...props}
    />
  </div>
);

const TextArea = ({ label, mono = false, ...props }) => (
  <div>
    {label && <label className="block text-sm font-semibold text-gray-300 mb-2">{label}</label>}
    <textarea
      className={`w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all text-gray-100 placeholder-gray-500 resize-none ${mono ? 'font-mono text-sm' : ''}`}
      {...props}
    />
  </div>
);

const Select = ({ label, options, ...props }) => (
  <div>
    {label && <label className="block text-sm font-semibold text-gray-300 mb-2">{label}</label>}
    <select
      className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-gray-100"
      {...props}
    >
      {options.map(opt => (
        <option key={opt} value={opt}>{opt || 'Select...'}</option>
      ))}
    </select>
  </div>
);

const Checkbox = ({ label, ...props }) => (
  <label className="flex items-center gap-2 cursor-pointer group">
    <input
      type="checkbox"
      className="w-4 h-4 rounded bg-gray-900/50 border-gray-700 text-blue-500 focus:ring-2 focus:ring-blue-500/50 cursor-pointer"
      {...props}
    />
    <span className="text-sm text-gray-300 group-hover:text-gray-100 transition-colors">{label}</span>
  </label>
);

const ApproachBox = ({ title, approach, onChange, fields, labels }) => (
  <div className="bg-gray-900/30 border border-gray-700/30 rounded-lg p-4">
    <h4 className="font-semibold text-gray-200 mb-3">{title}</h4>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {fields.map((field, idx) => (
        <Input
          key={field}
          label={labels[idx]}
          value={approach[field]}
          onChange={(e) => onChange(field, e.target.value)}
          placeholder={labels[idx]}
        />
      ))}
    </div>
  </div>
);

export default DSAMasteryTracker;