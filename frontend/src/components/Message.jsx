import { Fragment } from 'react'

const SAFE_PROTOCOLS = new Set(['http:', 'https:', 'mailto:'])

function isSafeUrl(url) {
  try {
    const parsed = new URL(url)
    return SAFE_PROTOCOLS.has(parsed.protocol)
  } catch {
    return false
  }
}

function parseInline(text) {
  const tokenPattern =
    /(\[([^\]]+)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)|`([^`]+)`|\*\*([^*]+)\*\*|__([^_]+)__|\*([^*]+)\*|_([^_]+)_)/g
  const nodes = []
  let cursor = 0
  let key = 0

  for (const match of text.matchAll(tokenPattern)) {
    const [fullMatch, , linkLabel, linkUrl, linkTitle, codeText, boldA, boldB, italicA, italicB] =
      match
    const index = match.index ?? 0

    if (index > cursor) {
      nodes.push(text.slice(cursor, index))
    }

    if (linkLabel && linkUrl) {
      if (isSafeUrl(linkUrl)) {
        nodes.push(
          <a key={`inline-${key}`} href={linkUrl} target="_blank" rel="noreferrer" title={linkTitle}>
            {parseInline(linkLabel)}
          </a>
        )
      } else {
        nodes.push(linkLabel)
      }
    } else if (codeText) {
      nodes.push(<code key={`inline-${key}`}>{codeText}</code>)
    } else if (boldA || boldB) {
      nodes.push(<strong key={`inline-${key}`}>{parseInline(boldA || boldB)}</strong>)
    } else if (italicA || italicB) {
      nodes.push(<em key={`inline-${key}`}>{parseInline(italicA || italicB)}</em>)
    } else {
      nodes.push(fullMatch)
    }

    cursor = index + fullMatch.length
    key += 1
  }

  if (cursor < text.length) {
    nodes.push(text.slice(cursor))
  }

  return nodes
}

function renderMarkdown(content) {
  const lines = content.split('\n')
  const blocks = []
  let index = 0

  while (index < lines.length) {
    const line = lines[index]
    const trimmed = line.trim()

    if (!trimmed) {
      index += 1
      continue
    }

    if (trimmed.startsWith('```')) {
      const language = trimmed.slice(3).trim()
      const codeLines = []
      index += 1

      while (index < lines.length && !lines[index].trim().startsWith('```')) {
        codeLines.push(lines[index])
        index += 1
      }

      if (index < lines.length) {
        index += 1
      }

      blocks.push(
        <pre key={`block-${blocks.length}`} className="message-code-block" data-language={language || undefined}>
          <code>{codeLines.join('\n')}</code>
        </pre>
      )
      continue
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/)
    if (headingMatch) {
      const level = headingMatch[1].length
      const HeadingTag = `h${level}`
      blocks.push(<HeadingTag key={`block-${blocks.length}`}>{parseInline(headingMatch[2])}</HeadingTag>)
      index += 1
      continue
    }

    if (/^(-{3,}|\*{3,})$/.test(trimmed)) {
      blocks.push(<hr key={`block-${blocks.length}`} />)
      index += 1
      continue
    }

    if (trimmed.startsWith('>')) {
      const quoteLines = []

      while (index < lines.length && lines[index].trim().startsWith('>')) {
        quoteLines.push(lines[index].trim().replace(/^>\s?/, ''))
        index += 1
      }

      blocks.push(
        <blockquote key={`block-${blocks.length}`}>
          {quoteLines.map((quoteLine, quoteIndex) => (
            <Fragment key={`quote-${quoteIndex}`}>
              {quoteIndex > 0 && <br />}
              {parseInline(quoteLine)}
            </Fragment>
          ))}
        </blockquote>
      )
      continue
    }

    if (/^[-*]\s+/.test(trimmed)) {
      const items = []

      while (index < lines.length && /^[-*]\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^[-*]\s+/, ''))
        index += 1
      }

      blocks.push(
        <ul key={`block-${blocks.length}`}>
          {items.map((item, itemIndex) => (
            <li key={`item-${itemIndex}`}>{parseInline(item)}</li>
          ))}
        </ul>
      )
      continue
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      const items = []

      while (index < lines.length && /^\d+\.\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^\d+\.\s+/, ''))
        index += 1
      }

      blocks.push(
        <ol key={`block-${blocks.length}`}>
          {items.map((item, itemIndex) => (
            <li key={`item-${itemIndex}`}>{parseInline(item)}</li>
          ))}
        </ol>
      )
      continue
    }

    const paragraphLines = [line]
    index += 1

    while (index < lines.length) {
      const nextTrimmed = lines[index].trim()

      if (
        !nextTrimmed ||
        nextTrimmed.startsWith('```') ||
        nextTrimmed.startsWith('>') ||
        /^#{1,6}\s+/.test(nextTrimmed) ||
        /^[-*]\s+/.test(nextTrimmed) ||
        /^\d+\.\s+/.test(nextTrimmed) ||
        /^(-{3,}|\*{3,})$/.test(nextTrimmed)
      ) {
        break
      }

      paragraphLines.push(lines[index])
      index += 1
    }

    blocks.push(
      <p key={`block-${blocks.length}`}>
        {paragraphLines.map((paragraphLine, paragraphIndex) => (
          <Fragment key={`line-${paragraphIndex}`}>
            {paragraphIndex > 0 && <br />}
            {parseInline(paragraphLine)}
          </Fragment>
        ))}
      </p>
    )
  }

  return blocks
}

const INTENT_LABELS = {
  factual: { label: 'Factual', color: '#1a5c38' },
  explanation: { label: 'Explanation', color: '#1a4a8a' },
  creative: { label: 'Creative', color: '#7b3fa0' },
}

function Message({ role, content, sources = [], intent = '' }) {
  const showSources = role === 'bot' && sources.length > 0
  const shouldRenderMarkdown = role === 'bot'
  const intentMeta = role === 'bot' && intent ? INTENT_LABELS[intent] : null

  return (
    <div className={`message message-${role}`}>
      <div className="message-avatar">
        {role === 'user' ? 'U' : 'N'}
      </div>
      <div className="message-body">
        <div className="message-name">
          {role === 'user' ? 'You' : 'NutriBot'}
          {intentMeta && (
            <span style={{
              marginLeft: '8px',
              fontSize: '11px',
              fontWeight: 600,
              padding: '2px 7px',
              borderRadius: '10px',
              background: intentMeta.color + '18',
              color: intentMeta.color,
              border: `1px solid ${intentMeta.color}40`,
              letterSpacing: '0.02em',
            }}>
              {intentMeta.label}
            </span>
          )}
        </div>
        <div className="message-bubble">
          {shouldRenderMarkdown ? (
            <div className="message-markdown">{renderMarkdown(content)}</div>
          ) : (
            <p style={{ whiteSpace: 'pre-wrap' }}>{content}</p>
          )}
        </div>
        {showSources && (
          <div className="message-sources">
            <div className="message-sources-label">Sources</div>
            <div className="source-list">
              {sources.map((source, index) => {
                const key = `${source.title}-${index}`

                if (!source.url) {
                  return (
                    <div key={key} className="source-card source-card-static" title={source.title}>
                      <span className="source-card-label">{source.title}</span>
                    </div>
                  )
                }

                return (
                  <a
                    key={key}
                    className="source-card"
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    title={source.title}
                  >
                    <span className="source-card-label">{source.title}</span>
                  </a>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Message
