import { useState, useEffect, useRef } from 'react';
import { useProjectContext } from '../context/ProjectContext';
import { documentsApi } from '../services/documentsApi';
import { Document } from '../services/types';

export function Documents() {
  const { activeProject } = useProjectContext();
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [drawerTab, setDrawerTab] = useState('chunks');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [chunks, setChunks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chunksError, setChunksError] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    if (!activeProject) {
      setDocuments([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const docs = await documentsApi.list(activeProject.project_id);
      setDocuments(docs || []);
    } catch (err: any) {
      setDocuments([]);
      setError(err instanceof TypeError ? 'Backend unavailable — could not load documents.' : `Failed to load documents: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    setSelected(null);
  }, [activeProject]);

  useEffect(() => {
    if (selected && drawerTab === 'chunks' && activeProject) {
      setChunksError(null);
      documentsApi.getSources(activeProject.project_id, selected).then(res => {
        setChunks(res.sources || []);
      }).catch(err => {
        setChunks([]);
        setChunksError(`Failed to load chunks: ${err.message}`);
      });
    }
  }, [selected, drawerTab, activeProject]);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !activeProject) return;
    
    setUploading(true);
    setError(null);
    try {
      const result = await documentsApi.upload(activeProject.project_id, file);
      if (result?.error) {
        setError(`Upload failed: ${result.error.message || result.error.code}`);
      }
      await fetchDocuments();
    } catch (err: any) {
      setError(err instanceof TypeError ? 'Upload failed: backend unavailable.' : `Upload failed: ${err.message || 'Unknown error'}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    if (!activeProject) return;
    try {
      await documentsApi.delete(activeProject.project_id, docId);
      if (selected === docId) setSelected(null);
      await fetchDocuments();
    } catch (err: any) {
      setError(`Delete failed: ${err.message || 'Unknown error'}`);
    }
  };

  const getDocName = (d: Document) => d.original_filename || d.filename || 'Unknown';

  const filtered = documents.filter(d =>
    getDocName(d).toLowerCase().includes(search.toLowerCase())
  );
  
  const selectedDoc = documents.find(d => d.document_id === selected);

  const getDocIcon = (d: Document) => {
    const ext = getDocName(d).split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return '📕';
    if (ext === 'docx') return '📘';
    if (ext === 'xlsx') return '📗';
    return '📄';
  };
  
  const getDocType = (d: Document) => {
    return getDocName(d).split('.').pop()?.toUpperCase() || 'FILE';
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', gap: 20 }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="section-label" style={{ marginBottom: 6 }}>Knowledge Base</div>
            <h1 className="font-display" style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>Document Library</h1>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input-field"
              placeholder="Search documents…"
              style={{ width: 220 }}
            />
            <button className="btn-secondary" style={{ fontSize: 12.5 }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="11" y2="18"/></svg>
              Filter
            </button>
            <input 
              type="file" 
              ref={fileInputRef} 
              style={{ display: 'none' }} 
              onChange={handleFileChange} 
              accept=".pdf,.docx,.txt,.xlsx,.csv,.png,.jpg,.jpeg"
            />
            <button className="btn-primary" style={{ fontSize: 12.5 }} onClick={handleUploadClick} disabled={uploading || !activeProject}>
              {uploading ? 'Uploading...' : (
                <>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                  Upload
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)', color: '#F87171', fontSize: 12.5 }}>
          {error} <button className="btn-ghost" style={{ fontSize: 12, marginLeft: 8 }} onClick={fetchDocuments}>Retry</button>
        </div>
      )}
      {loading ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <p style={{ color: 'var(--muted-foreground)' }}>Loading documents...</p>
        </div>
      ) : (!activeProject ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <p style={{ color: 'var(--muted-foreground)' }}>Please select a project to view documents.</p>
        </div>
      ) : (
        <div style={{ flex: 1, display: 'flex', gap: 20, overflow: 'hidden', minHeight: 0 }}>
          {/* Document list */}
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 0 }}>
            <div style={{ background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 12, overflow: 'hidden' }}>
              {/* Table header */}
              <div style={{
                display: 'grid', gridTemplateColumns: '1fr 72px 80px 100px 120px',
                padding: '10px 16px', borderBottom: '1px solid var(--border)',
                background: 'var(--surface-2)',
              }}>
                {['Filename', 'Type', 'Status', 'Updated', 'Actions'].map(h => (
                  <span key={h} style={{ fontSize: 11, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono', letterSpacing: '0.06em' }}>{h}</span>
                ))}
              </div>

              {filtered.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', color: 'var(--muted-foreground)' }}>
                  No documents found.
                </div>
              ) : (
                filtered.map(doc => {
                  const meta = doc.metadata || {};
                  const indexStatus = doc.index_status || meta.index_status;
                  const contentStatus = doc.content_status || meta.content_status;
                  
                  const isIndexed = indexStatus === 'indexed';
                  const isProcessing = indexStatus === 'requires_ocr' || contentStatus === 'pending';
                  const displayStatus = isIndexed ? 'indexed' : isProcessing ? 'processing' : 'stored';
                  
                  const docName = getDocName(doc);
                  
                  return (
                    <div
                      key={doc.document_id}
                      onClick={() => setSelected(doc.document_id)}
                      style={{
                        display: 'grid', gridTemplateColumns: '1fr 72px 80px 100px 120px',
                        padding: '12px 16px', borderBottom: '1px solid var(--border)',
                        cursor: 'pointer', transition: 'background 0.15s',
                        background: selected === doc.document_id ? 'var(--violet-dim)' : 'transparent',
                      }}
                      onMouseEnter={e => { if (selected !== doc.document_id) e.currentTarget.style.background = 'var(--surface-2)'; }}
                      onMouseLeave={e => { if (selected !== doc.document_id) e.currentTarget.style.background = 'transparent'; }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                        <span style={{ fontSize: 14, flexShrink: 0 }}>
                          {getDocIcon(doc)}
                        </span>
                        <span style={{ fontSize: 13, color: 'var(--foreground)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={docName}>{docName}</span>
                        {indexStatus === 'requires_ocr' && <span className="badge badge-teal" style={{ fontSize: 10, flexShrink: 0 }}>OCR</span>}
                      </div>
                      <span style={{ fontSize: 12, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono' }}>{getDocType(doc)}</span>
                      <span>
                        {displayStatus === 'indexed' && <span className="badge badge-green" style={{ fontSize: 10 }}>Indexed</span>}
                        {displayStatus === 'processing' && <span className="badge badge-amber" style={{ fontSize: 10 }}>Processing</span>}
                        {displayStatus === 'stored' && <span className="badge badge-gray" style={{ fontSize: 10 }}>Stored</span>}
                      </span>
                      <span style={{ fontSize: 11.5, color: 'var(--muted-foreground)' }}>{doc.created_at ? new Date(doc.created_at).toLocaleDateString() : '—'}</span>
                      <div style={{ display: 'flex', gap: 8 }} onClick={e => e.stopPropagation()}>
                        <a href={documentsApi.downloadUrl(activeProject.project_id, doc.document_id)} target="_blank" rel="noreferrer" className="btn-secondary" style={{ fontSize: 11, padding: '4px 8px' }}>DL</a>
                        <button onClick={() => handleDelete(doc.document_id)} className="btn-secondary" style={{ fontSize: 11, padding: '4px 8px', color: '#EF4444' }}>Del</button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Detail drawer */}
          {selected && selectedDoc && (
            <div style={{ width: 320, flexShrink: 0, background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 12, display: 'flex', flexDirection: 'column', overflow: 'hidden' }} className="doc-detail-panel">
              <div style={{ padding: '16px', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                  <span style={{ fontSize: 18 }}>{getDocIcon(selectedDoc)}</span>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', lineHeight: 1.3, wordBreak: 'break-all' }}>{getDocName(selectedDoc)}</div>
                    <div style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>{formatSize(selectedDoc.size_bytes || selectedDoc.metadata?.size_bytes)}</div>
                  </div>
                </div>
                <div className="tab-bar">
                  {['chunks', 'metadata'].map(t => (
                    <button key={t} onClick={() => setDrawerTab(t)} className={`tab-item ${drawerTab === t ? 'active' : ''}`}
                      style={{ flex: 1, textAlign: 'center', fontSize: 12 }}>
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {drawerTab === 'chunks' && chunks.map(chunk => (
                  <div key={chunk.chunk_id} style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 8, padding: '12px' }}>
                    <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap' }}>
                      <span className="badge badge-violet" style={{ fontSize: 10, wordBreak: 'break-all' }}>{chunk.chunk_id.substring(0, 16)}...</span>
                      {chunk.source?.page && <span className="badge badge-gray" style={{ fontSize: 10 }}>Page {chunk.source.page}</span>}
                    </div>
                    <p style={{ margin: 0, fontSize: 12, color: 'var(--muted-foreground)', lineHeight: 1.6 }}>{chunk.text}</p>
                  </div>
                ))}
                {drawerTab === 'chunks' && chunks.length === 0 && (
                  <div style={{ textAlign: 'center', padding: '32px', color: chunksError ? '#F87171' : 'var(--muted-foreground)', fontSize: 13 }}>
                    {chunksError || 'No chunks available or document not indexed.'}
                  </div>
                )}
                {drawerTab === 'metadata' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {[
                      { label: 'Type', value: getDocType(selectedDoc) },
                      { label: 'Content Status', value: selectedDoc.content_status || selectedDoc.metadata?.content_status || 'unknown' },
                      { label: 'Index Status', value: selectedDoc.index_status || selectedDoc.metadata?.index_status || 'unknown' },
                      { label: 'Size', value: formatSize(selectedDoc.size_bytes || selectedDoc.metadata?.size_bytes) },
                      { label: 'Created At', value: selectedDoc.created_at ? new Date(selectedDoc.created_at).toLocaleString() : '—' },
                    ].map(item => (
                      <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', background: 'var(--surface-2)', borderRadius: 7 }}>
                        <span style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>{item.label}</span>
                        <span className="font-mono" style={{ fontSize: 12, color: 'var(--foreground)' }}>{item.value}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ))}

      <style>{`
        @media (max-width: 900px) { .doc-detail-panel { display: none; } }
      `}</style>
    </div>
  );
}
