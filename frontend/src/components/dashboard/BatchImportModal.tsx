import React, { useState, useRef, useEffect } from "react"
import { UploadCloud, X, Loader2, CheckCircle2, AlertCircle, FileText } from "lucide-react"
import { uploadBatchCsv, checkImportStatus } from "../../services/productService"

interface BatchImportModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export default function BatchImportModal({ isOpen, onClose, onSuccess }: BatchImportModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<"pending" | "processing" | "completed" | "failed" | null>(null)
  const [error, setError] = useState("")
  const [jobDetails, setJobDetails] = useState<any>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!isOpen) {
      setFile(null)
      setIsUploading(false)
      setJobId(null)
      setJobStatus(null)
      setError("")
      setJobDetails(null)
    }
  }, [isOpen])

  // Polling mechanism
  useEffect(() => {
    let interval: any
    if (jobId && (jobStatus === "pending" || jobStatus === "processing")) {
      interval = setInterval(async () => {
        try {
          const res = await checkImportStatus(jobId)
          setJobStatus(res.status)
          setJobDetails(res)
          if (res.status === "completed" || res.status === "failed") {
            clearInterval(interval)
            setIsUploading(false)
            if (res.status === "completed") {
              onSuccess()
            }
          }
        } catch (err) {
          clearInterval(interval)
          setError("Gagal memeriksa status import.")
          setIsUploading(false)
        }
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [jobId, jobStatus, onSuccess])

  if (!isOpen) return null

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected) {
      if (selected.type !== "text/csv" && selected.type !== "application/vnd.ms-excel") {
        setError("Format file tidak didukung. Harap unggah file .csv")
        setFile(null)
      } else {
        setError("")
        setFile(selected)
      }
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setIsUploading(true)
    setError("")
    
    try {
      const res = await uploadBatchCsv(file)
      setJobId(res.job_id)
      setJobStatus("pending")
    } catch (err: any) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map((e: any) => e.msg).join(", "))
      } else {
        setError(detail || "Gagal mengunggah file.")
      }
      setIsUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md flex flex-col animate-in fade-in zoom-in-95 duration-200">
        
        <div className="flex items-center justify-between p-6 border-b border-slate-100">
          <h2 className="text-xl font-bold text-slate-900">Import Batch CSV</h2>
          <button 
            onClick={onClose} 
            disabled={isUploading}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          {!jobId ? (
            // State 1: Upload File
            <div className="space-y-4">
              <div 
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors ${
                  file ? "border-primary bg-primary/5" : "border-slate-300 hover:border-primary hover:bg-slate-50"
                }`}
              >
                <input 
                  type="file" 
                  accept=".csv" 
                  ref={fileInputRef} 
                  onChange={handleFileChange} 
                  className="hidden"
                />
                
                {file ? (
                  <>
                    <div className="w-12 h-12 bg-primary/10 text-primary rounded-full flex items-center justify-center mb-3">
                      <FileText className="w-6 h-6" />
                    </div>
                    <p className="text-sm font-medium text-slate-900 text-center">{file.name}</p>
                    <p className="text-xs text-slate-500 mt-1">{(file.size / 1024).toFixed(2)} KB</p>
                  </>
                ) : (
                  <>
                    <div className="w-12 h-12 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mb-3">
                      <UploadCloud className="w-6 h-6" />
                    </div>
                    <p className="text-sm font-medium text-slate-900 text-center">Pilih file CSV</p>
                    <p className="text-xs text-slate-500 mt-1 text-center">Tarik file ke sini atau klik untuk mencari</p>
                  </>
                )}
              </div>
              
              {error && (
                <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-100 rounded-md">
                  {error}
                </div>
              )}
              
              <div className="pt-2 text-xs text-slate-500 bg-slate-50 p-3 rounded-lg border border-slate-100">
                <p className="font-medium text-slate-700 mb-1">Format Kolom Wajib:</p>
                <code className="text-primary bg-primary/10 px-1 py-0.5 rounded">sku, name, category_id, supplier_id, price</code>
              </div>
            </div>
          ) : (
            // State 2: Progress Status
            <div className="py-6 flex flex-col items-center justify-center text-center space-y-4">
              {jobStatus === "pending" || jobStatus === "processing" ? (
                <>
                  <Loader2 className="w-12 h-12 text-primary animate-spin" />
                  <div>
                    <h3 className="text-lg font-medium text-slate-900">Memproses Data...</h3>
                    <p className="text-sm text-slate-500 mt-1">Sistem sedang memproses file CSV Anda.</p>
                  </div>
                </>
              ) : jobStatus === "completed" ? (
                <>
                  <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center">
                    <CheckCircle2 className="w-8 h-8" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-slate-900">Import Berhasil</h3>
                    <p className="text-sm text-slate-500 mt-1">
                      {jobDetails?.successful_rows || 0} baris berhasil ditambahkan.
                    </p>
                    {(jobDetails?.failed_rows || 0) > 0 && (
                      <p className="text-sm text-amber-600 mt-1 font-medium">
                        Catatan: {jobDetails.failed_rows} baris gagal diproses.
                      </p>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center">
                    <AlertCircle className="w-8 h-8" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-slate-900">Import Gagal</h3>
                    <p className="text-sm text-slate-500 mt-1">{jobDetails?.error || "Terjadi kesalahan yang tidak diketahui."}</p>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        <div className="p-6 border-t border-slate-100 bg-slate-50 rounded-b-xl flex justify-end gap-3">
          {jobStatus === "completed" || jobStatus === "failed" ? (
            <button 
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors"
            >
              Tutup
            </button>
          ) : (
            <>
              <button 
                onClick={onClose} disabled={isUploading}
                className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                Batal
              </button>
              <button 
                onClick={handleUpload} 
                disabled={!file || isUploading}
                className="px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isUploading && <Loader2 className="w-4 h-4 animate-spin" />}
                Mulai Import
              </button>
            </>
          )}
        </div>

      </div>
    </div>
  )
}
