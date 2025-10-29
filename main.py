import sys
import os
import tempfile
from pathlib import Path


# Настройка путей ДО импорта PyQt5
def get_resource_path(relative_path):
    """Получение правильного пути к ресурсам в standalone режиме"""
    try:
        # PyInstaller создает временную папку в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    full_path = os.path.join(base_path, relative_path)

    # Если файл не найден, пробуем альтернативные пути
    if not os.path.exists(full_path):
        # Пробуем относительно текущей директории
        alt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
        if os.path.exists(alt_path):
            return alt_path
        # Пробуем просто относительный путь
        elif os.path.exists(relative_path):
            return relative_path
        else:
            print(f"❌ Файл не найден: {relative_path}")
            print(f"   Пробовали пути:")
            print(f"   - {full_path}")
            print(f"   - {alt_path}")
            print(f"   - {relative_path}")
            return None

    return full_path


# Теперь импортируем PyQt5
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QPixmap, QKeySequence
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                             QFileDialog, QDialog, QShortcut)
from database import DatabaseManager

# Константы путей к UI файлам (будем получать через get_resource_path)
UI_MAIN_WINDOW = 'ui/main_window.ui'
UI_ORDER_DETAILS = 'ui/order_details.ui'
UI_DESSERT_DIALOG = 'ui/dessert_dialog.ui'


class OrderDetailsDialog(QDialog):
    """Диалог для отображения деталей заказа"""

    def __init__(self, order_data, parent=None):
        # Получаем правильный путь к UI файлу
        ui_path = get_resource_path(UI_ORDER_DETAILS)
        if not ui_path:
            QMessageBox.critical(parent, "Ошибка", f"Не найден файл интерфейса: {UI_ORDER_DETAILS}")
            return

        super().__init__(parent)
        uic.loadUi(ui_path, self)
        self.order_data = order_data
        self.setup_ui()
        self.load_order_data()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        self.loadPhotoBtn.clicked.connect(self.load_photo)
        self.clearPhotoBtn.clicked.connect(self.clear_photo)
        self.saveBtn.clicked.connect(self.save_changes)
        self.cancelBtn.clicked.connect(self.reject)

    def load_order_data(self):
        """Загрузка данных заказа в форму"""
        if self.order_data:
            self.orderIdLabel.setText(str(self.order_data[0]))
            self.clientLabel.setText(self.order_data[1])
            self.phoneLabel.setText(self.order_data[2])
            self.dessertsLabel.setText(self.order_data[3])
            self.dateLabel.setText(self.order_data[4])
            self.timeLabel.setText(self.order_data[5])
            self.deliveryLabel.setText(self.order_data[6])

            # Загрузка фото если есть
            photo_path = self.order_data[7] if len(self.order_data) > 7 else ""
            if photo_path and os.path.exists(photo_path):
                self.load_photo_from_path(photo_path)

    def load_photo(self):
        """Загрузка фото"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_name:
            self.load_photo_from_path(file_name)

    def load_photo_from_path(self, file_path):
        """Загрузка фото из указанного пути"""
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.photoLabel.width(),
                self.photoLabel.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.photoLabel.setPixmap(scaled_pixmap)
            self.photoLabel.setText("")

    def clear_photo(self):
        """Очистка фото"""
        self.photoLabel.clear()
        self.photoLabel.setText("Фото не загружено")

    def save_changes(self):
        """Сохранение изменений"""
        QMessageBox.information(self, "Успех", "Изменения сохранены!")
        self.accept()


class DessertDialog(QDialog):
    """Диалог для добавления/редактирования десертов"""

    def __init__(self, dessert_data=None, parent=None):
        # Получаем правильный путь к UI файлу
        ui_path = get_resource_path(UI_DESSERT_DIALOG)
        if not ui_path:
            QMessageBox.critical(parent, "Ошибка", f"Не найден файл интерфейса: {UI_DESSERT_DIALOG}")
            return

        super().__init__(parent)
        uic.loadUi(ui_path, self)
        self.dessert_data = dessert_data
        self.setup_ui()
        self.load_dessert_data()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        self.priceTypeCombo.currentIndexChanged.connect(self.on_price_type_changed)
        self.saveBtn.clicked.connect(self.save_dessert)
        self.cancelBtn.clicked.connect(self.reject)

        # Начальная настройка полей цены
        self.on_price_type_changed(0)

    def load_dessert_data(self):
        """Загрузка данных десерта в форму"""
        if self.dessert_data:
            self.nameEdit.setText(self.dessert_data[1])

            # Определение типа ценообразования
            price_kg = self.dessert_data[2] if self.dessert_data[2] else 0
            price_unit = self.dessert_data[3] if self.dessert_data[3] else 0

            if price_kg and price_unit:
                self.priceTypeCombo.setCurrentIndex(2)  # Оба варианта
            elif price_kg:
                self.priceTypeCombo.setCurrentIndex(0)  # За килограмм
            elif price_unit:
                self.priceTypeCombo.setCurrentIndex(1)  # За штуку

            self.priceKgEdit.setValue(float(price_kg))
            self.priceUnitEdit.setValue(float(price_unit))
            self.compositionEdit.setPlainText(self.dessert_data[4])

    def on_price_type_changed(self, index):
        """Обработка изменения типа ценообразования"""
        if index == 0:  # За килограмм
            self.priceKgEdit.setEnabled(True)
            self.priceUnitEdit.setEnabled(False)
            self.priceUnitEdit.setValue(0)
        elif index == 1:  # За штуку
            self.priceKgEdit.setEnabled(False)
            self.priceKgEdit.setValue(0)
            self.priceUnitEdit.setEnabled(True)
        else:  # Оба варианта
            self.priceKgEdit.setEnabled(True)
            self.priceUnitEdit.setEnabled(True)

    def save_dessert(self):
        """Сохранение десерта"""
        name = self.nameEdit.text().strip()
        price_kg = self.priceKgEdit.value()
        price_unit = self.priceUnitEdit.value()
        composition = self.compositionEdit.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название десерта!")
            return

        # Проверка что хотя бы одна цена указана
        if price_kg == 0 and price_unit == 0:
            QMessageBox.warning(self, "Ошибка", "Укажите хотя бы одну цену!")
            return

        self.saved_data = (name, price_kg, price_unit, composition)
        self.accept()

    def get_dessert_data(self):
        """Получение данных десерта"""
        return getattr(self, 'saved_data', None)


class ConfectioneryApp(QMainWindow):
    """Главное окно приложения кондитерской"""

    def __init__(self):
        super().__init__()

        # Получаем правильный путь к главному UI файлу
        ui_path = get_resource_path(UI_MAIN_WINDOW)
        if not ui_path:
            QMessageBox.critical(None, "Ошибка",
                                 f"Не найден главный файл интерфейса: {UI_MAIN_WINDOW}\n"
                                 f"Убедитесь, что папка 'ui' с файлами .ui находится рядом с приложением.")
            sys.exit(1)

        # Загружаем интерфейс
        uic.loadUi(ui_path, self)

        # Инициализация базы данных
        self.db = DatabaseManager()

        # Инициализация интерфейса
        self.init_ui()

        # Загрузка данных
        self.load_data()

        # Настройка горячих клавиш
        self.setup_shortcuts()

        print("✅ Приложение успешно инициализировано!")

    def load_ui(self):
        """Загрузка UI из файла"""
        # Этот метод больше не нужен, т.к. загрузка в __init__
        pass

    def init_ui(self):
        """Инициализация элементов интерфейса"""
        # Установка текущей даты и времени
        self.orderDateEdit.setDate(QDate.currentDate())
        self.orderTimeEdit.setTime(QTime.currentTime())
        self.clientBirthEdit.setDate(QDate(1990, 1, 1))

        # Заполнение комбобокса доставки
        self.deliveryCombo.addItems(["Доставка", "Самовывоз"])

        # Настройка таблиц
        self.setup_tables()

        # Подключение сигналов
        self.connect_signals()

        # Подключение сигналов меню
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.show_about)

    def setup_tables(self):
        """Настройка таблиц"""
        # Таблица заказов
        self.ordersTable.setHorizontalHeaderLabels([
            "ID", "Клиент", "Телефон", "Десерты", "Дата", "Время", "Тип"
        ])

        # Таблица клиентов
        self.clientsTable.setHorizontalHeaderLabels([
            "ID", "ФИО", "Телефон", "Дата рождения", "Email"
        ])

        # Таблица десертов
        self.dessertsTable.setHorizontalHeaderLabels([
            "ID", "Название", "Цена за кг", "Цена за шт", "Состав"
        ])

    def connect_signals(self):
        """Подключение сигналов к слотам"""
        # Заказы
        self.browsePhotoBtn.clicked.connect(self.browse_photo)
        self.addOrderBtn.clicked.connect(self.add_order)
        self.deleteOrderBtn.clicked.connect(self.delete_order)
        self.refreshOrdersBtn.clicked.connect(self.load_orders)
        self.ordersTable.itemDoubleClicked.connect(self.show_order_details)

        # Клиенты
        self.addClientBtn.clicked.connect(self.add_client)
        self.updateClientBtn.clicked.connect(self.update_client)
        self.deleteClientBtn.clicked.connect(self.delete_client)
        self.clearClientBtn.clicked.connect(self.clear_client_form)
        self.clientsTable.itemClicked.connect(self.client_table_clicked)

        # Десерты
        self.addDessertBtn.clicked.connect(self.add_dessert)
        self.updateDessertBtn.clicked.connect(self.update_dessert)
        self.deleteDessertBtn.clicked.connect(self.delete_dessert)
        self.clearDessertBtn.clicked.connect(self.clear_dessert_form)
        self.dessertsTable.itemClicked.connect(self.dessert_table_clicked)

    def setup_shortcuts(self):
        """Настройка горячих клавиш"""
        # Ctrl+Q для выхода
        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)

        # F5 для обновления данных
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.load_data)

        # Ctrl+N для нового заказа
        new_order_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_order_shortcut.activated.connect(self.clear_order_form)

    def load_data(self):
        """Загрузка всех данных"""
        self.load_clients()
        self.load_desserts()
        self.load_orders()

    def load_clients(self):
        """Загрузка клиентов в комбобокс и таблицу"""
        clients = self.db.get_all_clients()

        # Обновление комбобокса
        self.clientCombo.clear()
        for client in clients:
            self.clientCombo.addItem(f"{client[1]} ({client[2]})", client[0])

        # Обновление таблицы
        self.clientsTable.setRowCount(len(clients))
        for row, client in enumerate(clients):
            for col, data in enumerate(client):
                item = QtWidgets.QTableWidgetItem(str(data))
                self.clientsTable.setItem(row, col, item)

        self.clientsTable.resizeColumnsToContents()

    def load_desserts(self):
        """Загрузка десертов в чекбоксы и таблицу"""
        desserts = self.db.get_all_desserts()

        # Очистка layout с чекбоксами
        for i in reversed(range(self.dessertCheckboxLayout.count())):
            widget = self.dessertCheckboxLayout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Создание чекбоксов
        self.dessert_checkboxes = []
        for dessert in desserts:
            checkbox = QtWidgets.QCheckBox(dessert[1])
            checkbox.dessert_id = dessert[0]
            self.dessertCheckboxLayout.addWidget(checkbox)
            self.dessert_checkboxes.append(checkbox)

        # Обновление таблицы
        self.dessertsTable.setRowCount(len(desserts))
        for row, dessert in enumerate(desserts):
            for col, data in enumerate(dessert):
                item = QtWidgets.QTableWidgetItem(str(data))
                self.dessertsTable.setItem(row, col, item)

        self.dessertsTable.resizeColumnsToContents()

    def load_orders(self):
        """Загрузка заказов в таблицу"""
        orders = self.db.get_all_orders()

        self.ordersTable.setRowCount(len(orders))
        for row, order in enumerate(orders):
            for col, data in enumerate(order):
                item = QtWidgets.QTableWidgetItem(str(data))
                self.ordersTable.setItem(row, col, item)

        self.ordersTable.resizeColumnsToContents()

    def browse_photo(self):
        """Выбор фото для заказа"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_name:
            self.photoPathEdit.setText(file_name)
            pixmap = QPixmap(file_name)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.photoPreview.width(),
                    self.photoPreview.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.photoPreview.setPixmap(scaled_pixmap)

    def add_order(self):
        """Добавление нового заказа"""
        try:
            # Получение выбранного клиента
            if self.clientCombo.currentIndex() == -1:
                QMessageBox.warning(self, "Ошибка", "Выберите клиента!")
                return

            client_id = self.clientCombo.currentData()

            # Получение выбранных десертов
            selected_desserts = []
            for checkbox in self.dessert_checkboxes:
                if checkbox.isChecked():
                    selected_desserts.append(checkbox.text())

            if not selected_desserts:
                QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один десерт!")
                return

            dessert_types = ",".join(selected_desserts)

            # Получение даты и времени
            order_date = self.orderDateEdit.date().toString("yyyy-MM-dd")
            order_time = self.orderTimeEdit.time().toString("hh:mm")

            # Тип доставки
            delivery_type = self.deliveryCombo.currentText()

            # Путь к фото
            photo_path = self.photoPathEdit.text()

            # Добавление заказа в БД
            self.db.add_order(
                client_id, dessert_types, order_date,
                order_time, delivery_type, photo_path
            )

            QMessageBox.information(self, "Успех", "Заказ успешно добавлен!")
            self.load_orders()
            self.clear_order_form()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить заказ: {str(e)}")

    def delete_order(self):
        """Удаление выбранного заказа"""
        current_row = self.ordersTable.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ для удаления!")
            return

        order_id = int(self.ordersTable.item(current_row, 0).text())

        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить этот заказ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.db.delete_order(order_id)
            QMessageBox.information(self, "Успех", "Заказ удален!")
            self.load_orders()

    def show_order_details(self, item):
        """Показать детали заказа в диалоге"""
        row = item.row()
        order_data = [
            self.ordersTable.item(row, col).text()
            for col in range(self.ordersTable.columnCount())
        ]

        # Получение полных данных заказа из БД
        orders = self.db.get_all_orders()
        full_order_data = next((o for o in orders if str(o[0]) == order_data[0]), None)

        if full_order_data:
            dialog = OrderDetailsDialog(full_order_data, self)
            dialog.exec_()

    def add_client(self):
        """Добавление нового клиента"""
        try:
            full_name = self.clientNameEdit.text().strip()
            phone = self.clientPhoneEdit.text().strip()
            birth_date = self.clientBirthEdit.date().toString("yyyy-MM-dd")
            email = self.clientEmailEdit.text().strip()

            if not full_name or not phone:
                QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля (ФИО и телефон)!")
                return

            self.db.add_client(full_name, phone, birth_date, email)
            QMessageBox.information(self, "Успех", "Клиент успешно добавлен!")
            self.load_clients()
            self.clear_client_form()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить клиента: {str(e)}")

    def update_client(self):
        """Обновление данных клиента"""
        current_row = self.clientsTable.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента для обновления!")
            return

        try:
            client_id = int(self.clientsTable.item(current_row, 0).text())
            full_name = self.clientNameEdit.text().strip()
            phone = self.clientPhoneEdit.text().strip()
            birth_date = self.clientBirthEdit.date().toString("yyyy-MM-dd")
            email = self.clientEmailEdit.text().strip()

            if not full_name or not phone:
                QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля (ФИО и телефон)!")
                return

            self.db.update_client(client_id, full_name, phone, birth_date, email)
            QMessageBox.information(self, "Успех", "Данные клиента обновлены!")
            self.load_clients()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить клиента: {str(e)}")

    def delete_client(self):
        """Удаление клиента"""
        current_row = self.clientsTable.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента для удаления!")
            return

        client_id = int(self.clientsTable.item(current_row, 0).text())

        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить этого клиента?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.db.delete_client(client_id)
            QMessageBox.information(self, "Успех", "Клиент удален!")
            self.load_clients()
            self.clear_client_form()

    def client_table_clicked(self, item):
        """Заполнение формы данными выбранного клиента"""
        row = item.row()
        client_data = [
            self.clientsTable.item(row, col).text()
            for col in range(self.clientsTable.columnCount())
        ]

        self.clientNameEdit.setText(client_data[1])
        self.clientPhoneEdit.setText(client_data[2])

        # Парсинг даты рождения
        birth_date = QDate.fromString(client_data[3], "yyyy-MM-dd")
        if birth_date.isValid():
            self.clientBirthEdit.setDate(birth_date)

        self.clientEmailEdit.setText(client_data[4])

    def clear_client_form(self):
        """Очистка формы клиента"""
        self.clientNameEdit.clear()
        self.clientPhoneEdit.clear()
        self.clientBirthEdit.setDate(QDate(1990, 1, 1))
        self.clientEmailEdit.clear()

    def add_dessert(self):
        """Добавление нового десерта"""
        try:
            name = self.dessertNameEdit.text().strip()
            price_per_kg = self.dessertPriceKgEdit.value()
            price_per_unit = self.dessertPriceUnitEdit.value()
            composition = self.dessertCompositionEdit.toPlainText().strip()

            if not name:
                QMessageBox.warning(self, "Ошибка", "Введите название десерта!")
                return

            # Если обе цены 0, предупредить пользователя
            if price_per_kg == 0 and price_per_unit == 0:
                reply = QMessageBox.question(
                    self, "Подтверждение",
                    "Обе цены установлены в 0. Продолжить?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            self.db.add_dessert(name, price_per_kg, price_per_unit, composition)
            QMessageBox.information(self, "Успех", "Десерт успешно добавлен!")
            self.load_desserts()
            self.clear_dessert_form()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить десерт: {str(e)}")

    def update_dessert(self):
        """Обновление данных десерта"""
        current_row = self.dessertsTable.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите десерт для обновления!")
            return

        try:
            dessert_id = int(self.dessertsTable.item(current_row, 0).text())
            name = self.dessertNameEdit.text().strip()
            price_per_kg = self.dessertPriceKgEdit.value()
            price_per_unit = self.dessertPriceUnitEdit.value()
            composition = self.dessertCompositionEdit.toPlainText().strip()

            if not name:
                QMessageBox.warning(self, "Ошибка", "Введите название десерта!")
                return

            self.db.update_dessert(dessert_id, name, price_per_kg, price_per_unit, composition)
            QMessageBox.information(self, "Успех", "Данные десерта обновлены!")
            self.load_desserts()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить десерт: {str(e)}")

    def delete_dessert(self):
        """Удаление десерта"""
        current_row = self.dessertsTable.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите десерт для удаления!")
            return

        dessert_id = int(self.dessertsTable.item(current_row, 0).text())

        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить этот десерт?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.db.delete_dessert(dessert_id)
            QMessageBox.information(self, "Успех", "Десерт удален!")
            self.load_desserts()
            self.clear_dessert_form()

    def dessert_table_clicked(self, item):
        """Заполнение формы данными выбранного десерта"""
        row = item.row()
        dessert_data = [
            self.dessertsTable.item(row, col).text()
            for col in range(self.dessertsTable.columnCount())
        ]

        self.dessertNameEdit.setText(dessert_data[1])

        # Обработка цен
        price_kg = dessert_data[2] if dessert_data[2] != "None" else "0"
        price_unit = dessert_data[3] if dessert_data[3] != "None" else "0"

        self.dessertPriceKgEdit.setValue(float(price_kg))
        self.dessertPriceUnitEdit.setValue(float(price_unit))
        self.dessertCompositionEdit.setPlainText(dessert_data[4])

    def clear_dessert_form(self):
        """Очистка формы десерта"""
        self.dessertNameEdit.clear()
        self.dessertPriceKgEdit.setValue(0)
        self.dessertPriceUnitEdit.setValue(0)
        self.dessertCompositionEdit.clear()

    def clear_order_form(self):
        """Очистка формы заказа"""
        for checkbox in self.dessert_checkboxes:
            checkbox.setChecked(False)
        self.orderDateEdit.setDate(QDate.currentDate())
        self.orderTimeEdit.setTime(QTime.currentTime())
        self.deliveryCombo.setCurrentIndex(0)
        self.photoPathEdit.clear()
        self.photoPreview.clear()
        self.photoPreview.setText("Превью фото")

    def show_about(self):
        """Показать информацию о программе"""
        QMessageBox.about(self, "О программе",
                          "Кондитерская Sweet Dreams\n\n"
                          "Версия 1.0\n\n"
                          "Приложение для управления заказами кондитерской.\n"
                          "Разработано на PyQt5."
                          )

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_F1:
            QMessageBox.information(
                self, "Справка",
                "Кондитерская Sweet Dreams\n\n"
                "Горячие клавиши:\n"
                "F1 - Справка\n"
                "F5 - Обновить данные\n"
                "Ctrl+N - Новый заказ\n"
                "Ctrl+Q - Выход\n"
                "Esc - Закрыть приложение"
            )
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Обработка кликов мыши"""
        if event.button() == Qt.RightButton:
            # Контекстное меню по правому клику
            menu = QtWidgets.QMenu(self)

            refresh_action = menu.addAction("Обновить данные")
            new_order_action = menu.addAction("Новый заказ")
            menu.addSeparator()
            help_action = menu.addAction("Справка")
            exit_action = menu.addAction("Выход")

            action = menu.exec_(self.mapToGlobal(event.pos()))

            if action == refresh_action:
                self.load_data()
            elif action == new_order_action:
                self.tabWidget.setCurrentIndex(0)
                self.clear_order_form()
            elif action == help_action:
                self.keyPressEvent(type('Event', (), {'key': lambda: Qt.Key_F1})())
            elif action == exit_action:
                self.close()


def main():
    """Главная функция приложения"""
    app = QApplication(sys.argv)
    app.setApplicationName("Кондитерская Sweet Dreams")
    app.setApplicationVersion("1.0")

    # Создание и отображение главного окна
    window = ConfectioneryApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()