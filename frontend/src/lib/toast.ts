import { toast } from "sonner";

export const notify = {
  success: (message: string) => toast.success(message),
  error: (message: string) => toast.error(message),
  loading: (message: string) => toast.loading(message),
  dismiss: (id: string | number) => toast.dismiss(id),
};
