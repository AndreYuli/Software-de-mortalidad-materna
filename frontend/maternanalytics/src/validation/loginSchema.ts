import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Formato de correo inválido'),
  password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres'),
});
