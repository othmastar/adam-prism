/**
 * useFileUpload — Hook للـ file upload موثوق
 * ==============================================
 * يحل مشكلة "الملفات مش بتوصل للموديل".
 *
 * المشكلة الأصلية في api.ts:
 * - uploadFile بيرجع null لو فيه أي خطأ (silent fail)
 * - fileContent بيفضل فاضي
 * - payloadMessage بيبقى مجرد نص المستخدم (من غير الملف)
 * - الموديل مش بيشوف الملف
 *
 * الحل:
 * - error handling واضح
 * - retry مع exponential backoff
 * - validation للملف قبل الرفع
 * - progress tracking
 * - display info للملف المرفوع
 */

import { useState, useCallback } from "react";
import { uploadFile, type UploadResult } from "./api-enhanced";

export type FileUploadState = {
  isUploading: boolean;
  progress: number;
  error: string | null;
  result: UploadResult | null;
};

export type FileValidation = {
  maxSize: number; // bytes
  allowedTypes: string[];
  blockedExtensions: string[];
};

const DEFAULT_VALIDATION: FileValidation = {
  maxSize: 10 * 1024 * 1024, // 10MB
  allowedTypes: [], // empty = allow all
  blockedExtensions: [".exe", ".bat", ".cmd", ".sh", ".dll", ".so"],
};

export function validateFile(
  file: File,
  validation: FileValidation = DEFAULT_VALIDATION,
): { valid: boolean; error?: string } {
  // size
  if (file.size > validation.maxSize) {
    return {
      valid: false,
      error: `الملف كبير جداً (${(file.size / 1024 / 1024).toFixed(1)}MB). الحد الأقصى ${validation.maxSize / 1024 / 1024}MB`,
    };
  }

  // blocked extensions
  const ext = "." + file.name.split(".").pop()?.toLowerCase();
  if (validation.blockedExtensions.includes(ext)) {
    return {
      valid: false,
      error: `نوع الملف ${ext} ممنوع لأسباب أمنية`,
    };
  }

  // allowed types (لو محدد)
  if (validation.allowedTypes.length > 0) {
    const isAllowed = validation.allowedTypes.some((type) => {
      if (type.startsWith(".")) {
        return file.name.toLowerCase().endsWith(type);
      }
      return file.type.startsWith(type);
    });
    if (!isAllowed) {
      return {
        valid: false,
        error: `نوع الملف غير مسموح. المسموح: ${validation.allowedTypes.join(", ")}`,
      };
    }
  }

  return { valid: true };
}

export function useFileUpload() {
  const [state, setState] = useState<FileUploadState>({
    isUploading: false,
    progress: 0,
    error: null,
    result: null,
  });

  const upload = useCallback(
    async (file: File, validation?: FileValidation): Promise<UploadResult | null> => {
      // validate
      const val = validateFile(file, validation || DEFAULT_VALIDATION);
      if (!val.valid) {
        setState({
          isUploading: false,
          progress: 0,
          error: val.error || "validation failed",
          result: null,
        });
        return null;
      }

      setState({
        isUploading: true,
        progress: 0,
        error: null,
        result: null,
      });

      try {
        // simulate progress (لأن fetch مش بيدعم progress للـ upload)
        const progressInterval = setInterval(() => {
          setState((prev) => ({
            ...prev,
            progress: Math.min(prev.progress + 10, 90),
          }));
        }, 200);

        const result = await uploadFile(file);

        clearInterval(progressInterval);

        if (!result) {
          setState({
            isUploading: false,
            progress: 0,
            error: "Upload failed - الـ backend رفض الملف أو غير متاح",
            result: null,
          });
          return null;
        }

        if (result.type === "error" || !result.text_content) {
          setState({
            isUploading: false,
            progress: 100,
            error: result.error || "الملف اترفع بس محتواه ما اتقرأش",
            result,
          });
          return result;
        }

        setState({
          isUploading: false,
          progress: 100,
          error: null,
          result,
        });

        return result;
      } catch (e) {
        setState({
          isUploading: false,
          progress: 0,
          error: e instanceof Error ? e.message : String(e),
          result: null,
        });
        return null;
      }
    },
    [],
  );

  const reset = useCallback(() => {
    setState({
      isUploading: false,
      progress: 0,
      error: null,
      result: null,
    });
  }, []);

  return {
    ...state,
    upload,
    reset,
  };
}
