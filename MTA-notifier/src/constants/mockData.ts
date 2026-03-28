export const mockResponse = {
  station: "125th St",
  line: "A",
  status: "disrupted",
  last_updated: "3:42 PM",
  alerts: [
    {
      id: "1",
      type: "delay",
      severity: "high",
      message: "A train delayed 12 mins due to signal issues at 59th St",
      time: "3:41 PM"
    },
    {
      id: "2",
      type: "express_change",
      severity: "medium",
      message: "This A train is running local through Harlem",
      time: "3:38 PM"
    },
    {
      id: "3",
      type: "service_change",
      severity: "low",
      message: "A trains rerouted via F line until 6PM",
      time: "3:30 PM"
    }
  ]
}