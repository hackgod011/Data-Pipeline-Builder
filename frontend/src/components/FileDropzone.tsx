import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";

interface Props {
  onFilesAccepted: (files: File[]) => void;
  isUploading: boolean;
}

const ACCEPTED_TYPES = {
  "text/csv": [".csv"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/json": [".json"],
  "application/octet-stream": [".parquet"],
};

export default function FileDropzone({ onFilesAccepted, isUploading }: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => { if (accepted.length > 0) onFilesAccepted(accepted); },
    [onFilesAccepted]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    disabled: isUploading,
    multiple: true,
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200",
        isDragActive
          ? "border-indigo-500 bg-indigo-900/20"
          : "border-forge-border hover:border-forge-border-hover hover:bg-forge-surface2/50",
        isUploading && "opacity-60 cursor-not-allowed"
      )}
    >
      <input {...getInputProps()} />
      <AnimatePresence mode="wait">
        {isUploading ? (
          <motion.div
            key="uploading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            <div className="w-10 h-10 mx-auto rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
            <p className="text-sm text-slate-400">Uploading files…</p>
          </motion.div>
        ) : isDragActive ? (
          <motion.div
            key="drag"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-2"
          >
            <div className="w-12 h-12 mx-auto bg-indigo-600/20 rounded-xl flex items-center justify-center">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M12 19V5M5 12l7-7 7 7" stroke="#818CF8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <p className="text-sm font-medium text-indigo-400">Drop files here</p>
          </motion.div>
        ) : (
          <motion.div
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            <div className="w-12 h-12 mx-auto bg-forge-surface2 rounded-xl flex items-center justify-center border border-forge-border">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path d="M12 19V5M5 12l7-7 7 7" stroke="#64748B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-300">Drop files here, or click to browse</p>
              <p className="text-xs text-slate-500 mt-1">CSV · Excel · JSON · Parquet — max 1 GB each</p>
              <p className="text-xs text-indigo-400 mt-1">Multiple files supported</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
