# Verkada Command — Análisis Completo de Features

## Investigación realizada: 19 Mar 2026
**Objetivo:** Replicar funcionalidades clave de Verkada Command en DNS Vision AI

---

## 🎯 FEATURES DE VERKADA COMMAND (Completo)

### 📹 1. VIDEO SECURITY (Core)
| Feature | Descripción | DNS Vision AI | Prioridad |
|---------|-------------|---------------|-----------|
| Live View | Vista en vivo de cualquier cámara | ⬜ Pendiente | P1 |
| Historical Footage | Reproducción de video grabado | ⬜ Pendiente | P1 |
| Motion Search | Buscar eventos de movimiento en timeline | ⬜ Pendiente | P1 |
| Multi-camera View | Ver varias cámaras simultáneas | ⬜ Pendiente | P1 |
| Cloud + Local Storage | Almacenamiento híbrido | ⬜ Pendiente | P1 |
| Timelapse | Video acelerado de horas/días | ⬜ Pendiente | P2 |
| Video Sharing | Compartir clips por link/email | ⬜ Pendiente | P2 |
| Archive & Export | Archivar y exportar clips | ⬜ Pendiente | P2 |

### 🧠 2. AI ANALYTICS (Lo más importante)
| Feature | Descripción | DNS Vision AI | Prioridad |
|---------|-------------|---------------|-----------|
| People Detection | Detectar personas en frame | ✅ HECHO (Azure) | - |
| People Counting | Contar personas en frame | ⬜ Pendiente | P1 |
| Bounding Boxes | Rectángulos sobre personas/vehículos detectados | ⬜ Pendiente | P1 |
| Face Search | Buscar por cara específica | ⬜ Pendiente | P2 |
| Face Detection | Detectar y cropar caras | ⬜ Pendiente | P2 |
| Person Attributes | Filtrar por color de ropa, género, mochila | ⬜ Pendiente | P2 |
| People History | Historial de todas las personas detectadas | ⬜ Pendiente | P2 |
| Person of Interest (POI) | Lista de personas de interés con alertas | ⬜ Pendiente | P2 |
| AI-Powered Search | Búsqueda con lenguaje natural ("persona con chamarra azul") | ⬜ Pendiente | P3 |
| Reverse Image Search | Buscar subiendo una foto | ⬜ Pendiente | P3 |
| Unified Timeline | Seguir persona entre múltiples cámaras | ⬜ Pendiente | P3 |
| Vehicle Detection | Detectar vehículos | ⬜ Pendiente | P2 |
| License Plate Recognition (LPR) | Leer placas de vehículos | ❌ Descartado | - |
| License Plate of Interest | Alertas cuando aparece una placa específica | ❌ Descartado | - |
| LPR Zones | Monitorear ocupación de estacionamiento por placas | ❌ Descartado | - |
| Fighting Detection | Detectar peleas | ⬜ Pendiente | P3 |
| Person Falling Detection | Detectar caídas | ⬜ Pendiente | P3 |
| Loud Noise Detection | Detectar ruidos fuertes | ⬜ Pendiente | P3 |
| Loitering Detection | Detectar merodeo | ⬜ Pendiente | P2 |

### 🔥 3. HEATMAPS & OCCUPANCY
| Feature | Descripción | DNS Vision AI | Prioridad |
|---------|-------------|---------------|-----------|
| People Heatmaps | Mapa de calor de movimiento | ✅ HECHO | - |
| Heatmap on Floorplan | Heatmap sobre plano de piso | ⬜ Pendiente | P2 |
| Occupancy Trends | Tendencias de ocupación por hora/día | ⬜ Pendiente | P1 |
| Crowd Notifications | Alerta cuando hay más de X personas | ⬜ Pendiente | P1 |
| Queue Trends | Análisis de filas/colas | ⬜ Pendiente | P3 |
| Sales Conversion Trends | Conteo visitantes vs ventas | ⬜ Pendiente | P3 |

### 🚨 4. ALERTAS
| Feature | Descripción | DNS Vision AI | Prioridad |
|---------|-------------|---------------|-----------|
| Motion Alerts | Alerta por movimiento | ✅ HECHO | - |
| Person Detection Alert | Alerta cuando detecta persona | ✅ HECHO (WhatsApp) | - |
| Line Crossing Alert | Alerta cuando cruzan una línea virtual | 🔄 UI HECHA | P1 |
| Crowd Alert | Alerta por multitud (>N personas) | ⬜ Pendiente | P1 |
| Tailgating Alert | Alerta cuando alguien entra pegado a otro | ⬜ Pendiente | P2 |
| Compound Alerts | Combinar múltiples condiciones | ⬜ Pendiente | P3 |
| Smart List Alerts | Alerta por persona nueva o frecuente | ⬜ Pendiente | P3 |
| Alert via Email | Notificación por correo | ⬜ Pendiente | P1 |
| Alert via Push (Mobile) | Push notification en app | ⬜ Pendiente | P2 |
| Alert via WhatsApp | Notificación por WhatsApp | ✅ HECHO | - |
| Alert via Webhook | Webhook para integración | ⬜ Pendiente | P2 |
| Alert Trends Dashboard | Dashboard de tendencias de alertas | ⬜ Pendiente | P2 |

### 📐 5. ZONAS & FLOOR PLANS
| Feature | Descripción | DNS Vision AI | Prioridad |
|---------|-------------|---------------|-----------|
| Zone Editor | Dibujar zonas en cámara | ✅ HECHO | - |
| Detection per Zone | Configurar detección por zona | ✅ HECHO (UI) | P1 |
| Floor Plans | Subir planos de piso | ⬜ Pendiente | P2 |
| Camera Placement on Map | Ubicar cámaras en plano | ⬜ Pendiente | P2 |
| Heatmap on Floor Plan | Heatmap sobre plano | ⬜ Pendiente | P2 |
| Line Crossing Zones | Líneas de conteo virtual | ✅ HECHO (UI) | P1 |

### 📊 6. DASHBOARDS & REPORTS
| Feature | Descripción | DNS Vision AI | Prioridad |
|---------|-------------|---------------|-----------|
| Smart Trends Dashboard | Dashboard configurable con widgets | ⬜ Pendiente | P1 |
| Occupancy Widget | Widget de ocupación | ⬜ Pendiente | P1 |
| Alert Trends Widget | Widget de tendencias de alertas | ⬜ Pendiente | P2 |
| Device Stats Dashboard | Estado de salud de dispositivos | ⬜ Pendiente | P2 |
| Custom Reports | Reportes personalizados | ⬜ Pendiente | P2 |
| Incident Reports | Reportes de incidentes | ⬜ Pendiente | P2 |
| AI-Powered Summaries | Resumen automático de incidentes con IA | ⬜ Pendiente | P3 |

### 📱 7. MOBILE APP
| Feature | Descripción | DNS Vision AI | Prioridad |
|---------|-------------|---------------|-----------|
| Mobile Live View | Ver cámaras desde celular | ⬜ Pendiente | P2 |
| Push Notifications | Alertas push en celular | ⬜ Pendiente | P2 |
| Face Search Mobile | Buscar caras desde app | ⬜ Pendiente | P3 |
| Smart Trends Mobile | Dashboards en móvil | ⬜ Pendiente | P3 |

### 🔐 8. ACCESS CONTROL (Verkada tiene, nosotros podemos integrar)
| Feature | Descripción | DNS Vision AI | Prioridad |
|---------|-------------|---------------|-----------|
| Door Lock/Unlock | Control de puertas | ⬜ Futuro | P3 |
| Badge Events | Eventos de tarjeta | ⬜ Futuro | P3 |
| Visitor Management | Gestión de visitantes | ⬜ Futuro | P3 |
| Roll Call | Lista de personas presentes | ⬜ Futuro | P3 |

### 🛡️ 9. ALARMS & INTRUSION
| Feature | Descripción | DNS Vision AI | Prioridad |
|---------|-------------|---------------|-----------|
| Motion Sensors | Sensores de movimiento | ⬜ Futuro | P3 |
| Door Sensors | Sensores de puerta | ⬜ Futuro | P3 |
| Panic Buttons | Botones de pánico | ⬜ Futuro | P3 |
| AI-Powered Deterrence | Disuasión con voz IA | ⬜ Pendiente | P3 |
| Arm/Disarm Schedules | Horarios de armado | ⬜ Futuro | P3 |

### 🌡️ 10. ENVIRONMENTAL SENSORS
| Feature | Descripción | DNS Vision AI | Prioridad |
|---------|-------------|---------------|-----------|
| Air Quality Monitoring | Calidad del aire | ⬜ Futuro | P3 |
| Temperature Monitoring | Temperatura | ⬜ Futuro | P3 |
| Water Leak Detection | Detección de fugas | ⬜ Futuro | P3 |

### ⚙️ 11. PLATFORM & ADMIN
| Feature | Descripción | DNS Vision AI | Prioridad |
|---------|-------------|---------------|-----------|
| Multi-site Management | Gestión multi-sitio | ⬜ Pendiente | P1 |
| User Roles & Permissions | Roles y permisos | ⬜ Pendiente | P1 |
| Cloud Management | Gestión desde la nube | ⬜ Pendiente | P1 |
| API / Webhooks | API para integraciones | ⬜ Pendiente | P1 |
| Automatic Updates | Actualizaciones automáticas | ⬜ Pendiente | P2 |
| ONVIF Camera Support | Soporte cámaras terceros | ✅ HECHO | - |
| Command Connector | Integrar cámaras no-Verkada | ✅ HECHO (nuestro core) | - |
| SSO / SAML | Single sign-on | ⬜ Futuro | P3 |
| Audit Logs | Logs de auditoría | ⬜ Pendiente | P2 |

---

## 🏆 NUESTRAS VENTAJAS vs VERKADA

| DNS Vision AI | Verkada |
|---------------|---------|
| ✅ Compatible CUALQUIER cámara ONVIF | ❌ Solo cámaras Verkada (vendor lock-in) |
| ✅ On-premise (datos en tu server) | ☁️ Cloud obligatorio |
| ✅ Sin suscripción mensual por cámara | 💰 $199-$299 USD/cámara/año |
| ✅ Alertas por WhatsApp | ❌ Solo email/push app |
| ✅ Costo de IA bajo (Azure pay-per-use) | 💰 Incluido pero $$$$ |
| ✅ Personalizable 100% | ❌ Cerrado |

---

## 📋 ROADMAP DNS VISION AI

### Fase 1 — MVP (Actual, Mar 2026) ✅
- [x] Detección de personas (Azure AI)
- [x] Alertas WhatsApp
- [x] Heatmap de movimiento
- [x] Zone Editor (zonas + líneas)
- [x] Banco de imágenes
- [x] Video clips de eventos

### Fase 2 — Core Analytics (Abr 2026)
- [ ] People counting en tiempo real
- [ ] Conteo en línea virtual (tripwire)
- [ ] Bounding boxes en live view
- [ ] Occupancy trends (gráficas por hora/día)
- [ ] Crowd alerts (>N personas)
- [ ] Multi-camera view
- [ ] Live view en dashboard
- [ ] Historical playback
- [ ] Motion search timeline
- [ ] Alertas por email
- [ ] Multi-site management
- [ ] Roles y permisos

### Fase 3 — Advanced AI (May-Jun 2026)
- [ ] Face detection y búsqueda
- [ ] Person attributes (ropa, género)
- [ ] Person of Interest (POI) con alertas
- [ ] Vehicle detection
- [ ] LPR (lectura de placas)
- [ ] License Plate of Interest alerts
- [ ] Loitering detection
- [ ] EPP/Helmet detection
- [ ] Floor plans con cámaras
- [ ] Heatmap en floor plans
- [ ] Incident reports
- [ ] Dashboard con widgets configurables
- [ ] API REST completa
- [ ] Webhooks

### Fase 4 — Enterprise (Jul-Ago 2026)
- [ ] AI-Powered Search (lenguaje natural)
- [ ] Unified Timeline (tracking cross-camera)
- [ ] Reverse image search
- [ ] Fighting/falling detection
- [ ] Compound alerts
- [ ] Mobile app (PWA o React Native)
- [ ] Push notifications
- [ ] Timelapse
- [ ] AI-powered incident summaries
- [ ] AI-powered deterrence (voz)
- [ ] Queue/sales conversion analytics
- [ ] Audit logs
- [ ] SSO/SAML

---

## 💰 MODELO DE NEGOCIO PROPUESTO

### Verkada cobra:
- **Cámara + Licencia:** $599-$1,999 por cámara + $199-$299/año/cámara
- **20 cámaras:** ~$3,980-$5,980 USD/año solo en licencias

### DNS Vision AI puede cobrar:
- **Instalación + Configuración:** $X,XXX USD one-time
- **Licencia mensual:** $50-$100 USD/sitio (no por cámara)
- **Soporte:** $XXX USD/mes
- **Ventaja:** usa cámaras que ya tienen, sin vendor lock-in

---

*Documento generado por Ibra para DNS (Data Network Solutions)*
*Última actualización: 19 Mar 2026*
