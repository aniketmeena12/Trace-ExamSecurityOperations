// React Query hooks bound to the ACTIVE identity's token. Query keys include
// the active username so switching role in the demo refetches cleanly.
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useAuth } from "../auth/AuthContext";
import { api } from "./client";

function useActive() {
  const { token, active } = useAuth();
  return { token, username: active?.username };
}

export function useExams() {
  const { token, username } = useActive();
  return useQuery({
    queryKey: ["exams", username],
    queryFn: () => api.get("/exams", token),
    enabled: !!token,
  });
}

export function useUnlockStatus(examId, { poll = false } = {}) {
  const { token, username } = useActive();
  return useQuery({
    queryKey: ["unlock-status", examId, username],
    queryFn: () => api.get(`/exams/${examId}/unlock/status`, token),
    enabled: !!token && !!examId,
    refetchInterval: poll ? 1500 : false,
  });
}

export function useMyShare(examId) {
  const { token, username } = useActive();
  return useQuery({
    queryKey: ["my-share", examId, username],
    queryFn: () => api.get(`/exams/${examId}/my-share`, token),
    enabled: !!token && !!examId,
    retry: false,
    refetchInterval: 1500,
  });
}

export function usePaperImage(examId, enabled) {
  const { token, username } = useActive();
  return useQuery({
    queryKey: ["paper-image", examId, username],
    queryFn: () => api.getImage(`/exams/${examId}/paper/image`, token),
    enabled: !!token && !!examId && !!enabled,
    staleTime: Infinity, // the watermarked PNG is stable per candidate
    retry: false,
  });
}

export function useQuestions(subject) {
  const { token, username } = useActive();
  return useQuery({
    queryKey: ["questions", subject, username],
    queryFn: () =>
      api.get(`/questions${subject ? `?subject=${encodeURIComponent(subject)}` : ""}`, token),
    enabled: !!token,
  });
}

export function useBlueprint(examId, enabled = true) {
  const { token, username } = useActive();
  return useQuery({
    queryKey: ["blueprint", examId, username],
    queryFn: () => api.get(`/exams/${examId}/blueprint`, token),
    enabled: !!token && !!examId && enabled,
    retry: false,
  });
}

export function useAudit() {
  const { token, username } = useActive();
  return useQuery({
    queryKey: ["audit", username],
    queryFn: () => api.get("/audit", token),
    enabled: !!token,
  });
}

export function useCreateExam() {
  const { token } = useActive();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) => api.post("/exams", token, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["exams"] }),
  });
}

export function useSubmitShare(examId) {
  const { token } = useActive();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post(`/exams/${examId}/shares/submit`, token),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["unlock-status", examId] });
      qc.invalidateQueries({ queryKey: ["my-share", examId] });
      qc.invalidateQueries({ queryKey: ["audit"] });
    },
  });
}

export function useVerifyChain() {
  const { token } = useActive();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.get("/audit/verify", token),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["audit"] }),
  });
}

export function useTrace() {
  const { token } = useActive();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file) => api.uploadImage("/investigator/trace", token, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["audit"] }),
  });
}

export function useLeakMatch() {
  const { token } = useActive();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (text) => api.post("/investigator/match", token, { text }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["audit"] }),
  });
}
