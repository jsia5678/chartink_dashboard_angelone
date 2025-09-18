// Chartink Backtesting Dashboard JavaScript

class BacktestDashboard {
    constructor() {
        this.uploadedData = null;
        this.backtestResults = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // File upload handling
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');
        const runBacktestBtn = document.getElementById('runBacktestBtn');
        const exportBtn = document.getElementById('exportBtn');

        fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        
        // Drag and drop functionality
        uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        uploadArea.addEventListener('click', () => fileInput.click());

        runBacktestBtn.addEventListener('click', () => this.runBacktest());
        exportBtn.addEventListener('click', () => this.exportResults());
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileUpload(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    async processFile(file) {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            this.showAlert('Please upload a CSV file', 'danger');
            return;
        }

        this.showAlert('Uploading file...', 'info');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.uploadedData = result;
                this.showAlert(result.message, 'success');
                this.showParametersSection();
            } else {
                this.showAlert(result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Error uploading file: ' + error.message, 'danger');
        }
    }

    showParametersSection() {
        document.getElementById('parametersSection').style.display = 'block';
    }

    async runBacktest() {
        if (!this.uploadedData) {
            this.showAlert('Please upload a CSV file first', 'warning');
            return;
        }
        
        const holdingDays = parseInt(document.getElementById('holdingDays').value);

        // Validate parameters
        if (holdingDays <= 0) {
            this.showAlert('Please enter valid holding days', 'warning');
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch('/run_backtest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    holding_days: holdingDays
                })
            });

            const result = await response.json();

            if (result.success) {
                this.backtestResults = result;
                this.displayResults(result);
                this.showAlert('Backtest completed successfully!', 'success');
            } else {
                this.showAlert(result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Error running backtest: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }


    displayResults(results) {
        // Update metrics
        this.updateMetrics(results.metrics);
        
        // Show results section
        document.getElementById('resultsSection').style.display = 'block';
        
        // Scroll to results
        document.getElementById('resultsSection').scrollIntoView({ 
            behavior: 'smooth' 
        });
    }

    updateMetrics(metrics) {
        document.getElementById('winRate').textContent = metrics.win_rate || '-';
        document.getElementById('totalTrades').textContent = metrics.total_trades || '-';
        document.getElementById('avgReturn').textContent = metrics.avg_return || '-';
        document.getElementById('totalReturn').textContent = metrics.total_return || '-';
        document.getElementById('bestTrade').textContent = metrics.best_trade || '-';
        document.getElementById('worstTrade').textContent = metrics.worst_trade || '-';
    }


    async exportResults() {
        if (!this.backtestResults) {
            this.showAlert('No results to export', 'warning');
            return;
        }

        try {
            const response = await fetch('/export_results');
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `backtest_results_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showAlert('Results exported successfully!', 'success');
            } else {
                const error = await response.json();
                this.showAlert(error.error || 'Error exporting results', 'danger');
            }
        } catch (error) {
            this.showAlert('Error exporting results: ' + error.message, 'danger');
        }
    }

    showLoading(show) {
        const loadingSection = document.getElementById('loadingSection');
        const resultsSection = document.getElementById('resultsSection');
        
        if (show) {
            loadingSection.style.display = 'block';
            resultsSection.style.display = 'none';
        } else {
            loadingSection.style.display = 'none';
        }
    }

    showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer');
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-custom`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new BacktestDashboard();
});

// Utility functions
function formatNumber(num, decimals = 2) {
    return parseFloat(num).toFixed(decimals);
}

function formatPercentage(num, decimals = 2) {
    return formatNumber(num, decimals) + '%';
}

// Handle page visibility change to pause/resume animations
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, pause any animations
        console.log('Page hidden - pausing animations');
    } else {
        // Page is visible, resume animations
        console.log('Page visible - resuming animations');
    }
});
