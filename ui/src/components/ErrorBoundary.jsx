import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { crashed: false, message: '' }
  }

  static getDerivedStateFromError(err) {
    return { crashed: true, message: err?.message || 'Unknown error' }
  }

  render() {
    if (this.state.crashed) {
      return (
        <div className="job-card job-card--error">
          <div className="job-card-header">
            <span className="job-filename">Something went wrong</span>
            <span className="job-status-badge error">✕ Error</span>
          </div>
          <p className="job-error-msg">{this.state.message}</p>
        </div>
      )
    }
    return this.props.children
  }
}
