from dataclasses import dataclass


@dataclass(slots=True)
class PortPlan:
    """
    Read-only assessment of physical connection capacity.
    """

    total_usb_ports: int
    used_usb_ports: int

    reserved_shuttle_ports: int = 1
    reserved_input_ports: int = 1
    reserved_recovery_ports: int = 1

    total_sata_ports: int = 0
    used_sata_ports: int = 0

    @property
    def reserved_usb_ports(self):
        return (
            self.reserved_shuttle_ports
            + self.reserved_input_ports
            + self.reserved_recovery_ports
        )

    @property
    def free_usb_ports(self):
        return max(
            0,
            self.total_usb_ports - self.used_usb_ports,
        )

    @property
    def usable_usb_ports(self):
        """
        USB ports available for permanent devices after reserves.
        """

        return max(
            0,
            self.free_usb_ports - self.reserved_usb_ports,
        )

    @property
    def free_sata_ports(self):
        return max(
            0,
            self.total_sata_ports - self.used_sata_ports,
        )

    @property
    def usb_reserve_satisfied(self):
        return self.free_usb_ports >= self.reserved_usb_ports


def recommend_connection(plan: PortPlan, role: str):
    """
    Recommend a connection type for a new storage device.

    Advisory only. No hardware or configuration is changed.
    """

    role = role.strip().lower()

    if role in {"library", "expansion"}:
        if plan.free_sata_ports > 0:
            return "SATA", (
                "Use an internal SATA connection to preserve USB ports "
                "for shuttles and removable devices"
            )

        if plan.usable_usb_ports > 0:
            return "USB", (
                "No SATA port is available; one USB port can be used "
                "without consuming the reserved ports"
            )

        return "NONE", (
            "No suitable port is available while maintaining the "
            "configured USB reserve"
        )

    if role == "shuttle":
        if plan.free_usb_ports > 0:
            return "USB", "Use a direct high-speed USB connection"

        return "NONE", "No USB port is currently available"

    if role in {"backup", "archive"}:
        if plan.free_sata_ports > 0:
            return "SATA", (
                "An internal connection is available and preserves USB ports"
            )

        if plan.usable_usb_ports > 0:
            return "USB", (
                "A removable USB backup can be added while preserving reserves"
            )

        return "NONE", (
            "Add a SATA controller, powered enclosure, or other expansion "
            "before attaching this drive"
        )

    return "REVIEW", f"Unknown storage role: {role}"


def show_port_plan(plan: PortPlan):
    print()
    print("Port Capacity")
    print("═════════════")

    print()
    print("USB")
    print("───")
    print(f"Total               {plan.total_usb_ports}")
    print(f"In use              {plan.used_usb_ports}")
    print(f"Free                {plan.free_usb_ports}")
    print(f"Reserved            {plan.reserved_usb_ports}")
    print(f"Permanent available {plan.usable_usb_ports}")

    print()
    print("SATA")
    print("────")
    print(f"Total               {plan.total_sata_ports}")
    print(f"In use              {plan.used_sata_ports}")
    print(f"Free                {plan.free_sata_ports}")

    print()
    print("Status")
    print("──────")

    if plan.usb_reserve_satisfied:
        print("✓ Required USB reserve is available")
    else:
        print("⚠ Required USB reserve is not available")

    print()
    print("Assessment only. Nothing has been changed.")
