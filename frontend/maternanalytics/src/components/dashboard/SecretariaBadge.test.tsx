import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SecretariaBadge } from "./SecretariaBadge";

describe("SecretariaBadge", () => {
  it("muestra el municipio derivado del nombre completo de la secretaría", () => {
    render(<SecretariaBadge secretaria="Secretaría de Salud de Bello" />);
    expect(screen.getByText("Bello")).toBeInTheDocument();
    expect(
      screen.getByLabelText(
        "Secretaría de salud: Secretaría de Salud de Bello",
      ),
    ).toBeInTheDocument();
  });

  it("no se renderiza cuando no hay secretaría (cuentas sin tenant)", () => {
    const { container } = render(<SecretariaBadge secretaria={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});
