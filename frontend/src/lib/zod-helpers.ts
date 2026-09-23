import { z } from "zod"

/**
 * Número opcional vindo de um <input>. Um campo vazio chega como "" e `z.coerce.number()` o
 * transforma em 0 — que falha em `.min(1)` sem mensagem visível (o envio simplesmente não
 * acontecia) ou vai para a API como 0 em vez de "não informado".
 */
export function optionalNumber<T extends z.ZodTypeAny>(schema: T): z.ZodOptional<T> {
  // O cast mantém o tipo de entrada igual ao de `schema.optional()` (o preprocess o tornaria
  // `unknown`, incompatível com os tipos do react-hook-form); o comportamento em runtime é o do
  // preprocess.
  return z.preprocess(
    (value) => (value === "" || value === null || (typeof value === "number" && Number.isNaN(value)) ? undefined : value),
    schema.optional(),
  ) as unknown as z.ZodOptional<T>
}
