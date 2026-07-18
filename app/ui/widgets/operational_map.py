"""Composant cartographique léger, utilisable sans service en ligne."""

from math import cos, radians

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsScene, QGraphicsView


class OperationalMap(QGraphicsView):
    """Carte vectorielle avec zoom, déplacement et sélection de marqueurs."""

    itemSelected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._items, self._marker_items = [], {}
        self._dragging = False
        self._last_mouse_pos = None
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setBackgroundBrush(QColor("#e8f1f5"))

    def set_items(self, items):
        self._items = list(items)
        self._marker_items.clear()
        self._scene.clear()
        if not self._items:
            return
        latitudes = [item.latitude for item in self._items]
        longitudes = [item.longitude for item in self._items]
        self._bounds = min(latitudes), max(latitudes), min(longitudes), max(longitudes)
        self._draw_grid()
        for item in self._items:
            marker = self._create_marker(item)
            self._marker_items[marker] = item
        self.fit_to_items()

    def fit_to_items(self):
        if not self._items:
            self.resetTransform()
            return
        rect = self._scene.itemsBoundingRect().adjusted(-45, -45, 45, 45)
        if rect.width() < 1 or rect.height() < 1:
            rect = QRectF(rect.center().x() - 50, rect.center().y() - 50, 100, 100)
        self.fitInView(rect, Qt.KeepAspectRatio)

    def _to_point(self, latitude, longitude):
        min_lat, max_lat, min_lon, max_lon = self._bounds
        span_lat, span_lon = max(max_lat - min_lat, 0.002), max(max_lon - min_lon, 0.002)
        x = ((longitude - min_lon) / span_lon) * 1000 * cos(radians((min_lat + max_lat) / 2))
        y = -((latitude - min_lat) / span_lat) * 1000
        return QPointF(x, y)

    def _draw_grid(self):
        min_lat, max_lat, min_lon, max_lon = self._bounds
        rect = QRectF(self._to_point(max_lat, min_lon), self._to_point(min_lat, max_lon)).normalized().adjusted(-25, -25, 25, 25)
        pen = QPen(QColor("#cbd5e1"), 1)
        for fraction in range(6):
            x, y = rect.left() + rect.width() * fraction / 5, rect.top() + rect.height() * fraction / 5
            self._scene.addLine(x, rect.top(), x, rect.bottom(), pen)
            self._scene.addLine(rect.left(), y, rect.right(), y, pen)

    def _create_marker(self, item):
        marker = QGraphicsEllipseItem(-9, -9, 18, 18)
        marker.setPos(self._to_point(item.latitude, item.longitude))
        marker.setBrush(QColor(item.color or "#2563eb"))
        marker.setPen(QPen(QColor("white"), 2))
        marker.setFlag(QGraphicsEllipseItem.ItemIsSelectable)
        marker.setToolTip(f"{item.title}\n{item.subtitle}")
        self._scene.addItem(marker)
        return marker

    def wheelEvent(self, event):
        self.scale(1.2 if event.angleDelta().y() > 0 else 1 / 1.2, 1.2 if event.angleDelta().y() > 0 else 1 / 1.2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item in self._marker_items:
                self.itemSelected.emit(self._marker_items[item])
            else:
                self._dragging, self._last_mouse_pos = True, event.pos()
                self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._last_mouse_pos is not None:
            delta, self._last_mouse_pos = event.pos() - self._last_mouse_pos, event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragging, self._last_mouse_pos = False, None
        self.unsetCursor()
        super().mouseReleaseEvent(event)
