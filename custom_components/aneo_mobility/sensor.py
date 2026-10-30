"""Platform for sensor integration."""

from __future__ import annotations

import logging

from homeassistant import config_entries, core
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.helpers.entity import EntityCategory

from .base import AneoMobilityEntity
from .const import (
    COORDINATOR_CHARGER_STATE,
    COORDINATOR_PRICE_DATA,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors and configure coordinator."""
    coordinators = hass.data[DOMAIN][config_entry.entry_id]["coordinators"]
    charge_state_coordinator = coordinators[COORDINATOR_CHARGER_STATE]
    price_data_coordinator = coordinators[COORDINATOR_PRICE_DATA]

    sensors = []

    # Create charger sensors for each charger
    if charge_state_coordinator.data:
        for charger_id in charge_state_coordinator.data.keys():
            sensors.append(
                ChargerRawStateSensor(
                    charge_state_coordinator, config_entry, charger_id
                )
            )
            sensors.append(ActualSocketStatus(charge_state_coordinator, config_entry, charger_id))

    # Create price sensor (only one, not per-charger)
    sensors.append(PriceSensor(price_data_coordinator, config_entry))

    async_add_entities(sensors, update_before_add=True)


class ChargerRawStateSensor(AneoMobilityEntity, SensorEntity):
    """Sensor for raw charger status."""

    _attr_translation_key = "raw_charger_status"
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator, config_entry, charger_id):
        """Initialize the sensor."""
        super().__init__(
            coordinator, config_entry, charger_id
        )  # ← Must pass charger_id!

    @property
    def native_value(self):
        """Get value from data returned from API by coordinator."""
        if self.coordinator.data is None:
            return None

        charger_data = self.coordinator.data.get(self._charger_id)
        if not charger_data:
            return None

        state = charger_data.get("state", {})
        sockets = state.get("sockets", [])

        if not sockets:
            return None

        socket_status = sockets[0].get("status")

        # Map to friendly state
        if socket_status == "Charging":
            return "charging"
        elif socket_status == "Preparing":
            return "ready"
        else:  # Finishing or anything else
            return "stopped"


class ActualSocketStatus(AneoMobilityEntity, SensorEntity):
    """Untranslated socket status reported by the Joulia API."""

    _attr_translation_key = "actual_socket_status"
    _attr_name = "Joulia socket status"
    _attr_icon = "mdi:ev-station"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        charger = data.get(self._charger_id) or {}
        sockets = (charger.get("state") or {}).get("sockets") or []
        return sockets[0].get("status") if sockets and isinstance(sockets[0], dict) else None


class PriceSensor(AneoMobilityEntity, SensorEntity):
    """Sensor for price data."""

    _attr_translation_key = "price"
    _attr_icon = "mdi:cash"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = 2
    _attr_native_unit_of_measurement = "NOK/kWh"

    def __init__(self, coordinator, config_entry):
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)  # No charger_id

    @property
    def native_value(self):
        """Get value from data returned from API by coordinator."""
        if self.coordinator.data:
            return self.coordinator.data.get("current_price")
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        if self.coordinator.data:
            return self.coordinator.data.get("extra_attributes", {})
        return {}
