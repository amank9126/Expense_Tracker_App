import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
import sqlite3
import pandas as pd
from datetime import datetime
import os

# Android-specific imports
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    
    # Request permissions
    request_permissions([
        Permission.WRITE_EXTERNAL_STORAGE, 
        Permission.READ_EXTERNAL_STORAGE
    ])

class ExpenseTrackerApp(App):
    def build(self):
        self.title = "Expense Tracker"
        self.setup_database()
        
        # Main layout with better spacing for mobile
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Title
        title = Label(text='Expense Tracker', size_hint_y=None, height=60, 
                     font_size=28, bold=True)
        main_layout.add_widget(title)
        
        # Salary section
        salary_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        salary_layout.add_widget(Label(text='Monthly Salary:', size_hint_x=0.3, font_size=16))
        self.salary_input = TextInput(multiline=False, size_hint_x=0.5, font_size=16)
        salary_layout.add_widget(self.salary_input)
        set_salary_btn = Button(text='Set', size_hint_x=0.2, font_size=14)
        set_salary_btn.bind(on_press=self.set_salary)
        salary_layout.add_widget(set_salary_btn)
        main_layout.add_widget(salary_layout)
        
        # Balance display
        self.balance_label = Label(text='Current Balance: $0.00', size_hint_y=None, 
                                  height=50, font_size=18, bold=True)
        main_layout.add_widget(self.balance_label)
        
        # Expense input section
        expense_layout = GridLayout(cols=2, size_hint_y=None, height=240, spacing=10)
        
        expense_layout.add_widget(Label(text='Amount:', font_size=16))
        self.amount_input = TextInput(multiline=False, input_filter='float', font_size=16)
        expense_layout.add_widget(self.amount_input)
        
        expense_layout.add_widget(Label(text='Category:', font_size=16))
        self.category_spinner = Spinner(
            text='Select Category',
            values=['Food', 'Transportation', 'Entertainment', 'Shopping', 
                   'Bills', 'Healthcare', 'Education', 'Other'],
            font_size=16
        )
        expense_layout.add_widget(self.category_spinner)
        
        expense_layout.add_widget(Label(text='Description:', font_size=16))
        self.description_input = TextInput(multiline=False, font_size=16)
        expense_layout.add_widget(self.description_input)
        
        expense_layout.add_widget(Label(text='Date:', font_size=16))
        self.date_input = TextInput(multiline=False, text=datetime.now().strftime('%Y-%m-%d'), font_size=16)
        expense_layout.add_widget(self.date_input)
        
        main_layout.add_widget(expense_layout)
        
        # Main action buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)
        
        add_btn = Button(text='Add Expense', font_size=16)
        add_btn.bind(on_press=self.add_expense)
        button_layout.add_widget(add_btn)
        
        view_btn = Button(text='View Expenses', font_size=16)
        view_btn.bind(on_press=self.view_expenses)
        button_layout.add_widget(view_btn)
        
        main_layout.add_widget(button_layout)
        
        # Secondary buttons
        button_layout2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)
        
        export_btn = Button(text='Export Excel', font_size=16)
        export_btn.bind(on_press=self.export_to_excel)
        button_layout2.add_widget(export_btn)
        
        total_btn = Button(text='Statistics', font_size=16)
        total_btn.bind(on_press=self.show_statistics)
        button_layout2.add_widget(total_btn)
        
        main_layout.add_widget(button_layout2)
        
        # Update balance on startup
        Clock.schedule_once(self.update_balance, 0.1)
        
        return main_layout
    
    def get_app_directory(self):
        """Get appropriate directory for app data"""
        if platform == 'android':
            from android.storage import app_storage_path
            return app_storage_path()
        else:
            return os.getcwd()
    
    def get_export_directory(self):
        """Get appropriate directory for exports"""
        if platform == 'android':
            try:
                return primary_external_storage_path()
            except:
                return self.get_app_directory()
        else:
            return os.getcwd()
    
    def setup_database(self):
        """Initialize SQLite database"""
        db_path = os.path.join(self.get_app_directory(), 'expenses.db')
        self.conn = sqlite3.connect(db_path)
        cursor = self.conn.cursor()
        
        # Create expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create salary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS salary (
                id INTEGER PRIMARY KEY,
                amount REAL NOT NULL,
                month TEXT NOT NULL,
                UNIQUE(month)
            )
        ''')
        
        self.conn.commit()
    
    def set_salary(self, instance):
        """Set monthly salary"""
        try:
            amount = float(self.salary_input.text)
            current_month = datetime.now().strftime('%Y-%m')
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO salary (id, amount, month)
                VALUES (1, ?, ?)
            ''', (amount, current_month))
            
            self.conn.commit()
            self.update_balance()
            self.show_popup('Success', f'Salary set to ${amount:.2f}')
            
        except ValueError:
            self.show_popup('Error', 'Please enter a valid salary amount')
    
    def add_expense(self, instance):
        """Add new expense"""
        try:
            amount = float(self.amount_input.text)
            category = self.category_spinner.text
            description = self.description_input.text
            date = self.date_input.text
            
            if category == 'Select Category':
                self.show_popup('Error', 'Please select a category')
                return
            
            # Validate date format
            datetime.strptime(date, '%Y-%m-%d')
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO expenses (amount, category, description, date)
                VALUES (?, ?, ?, ?)
            ''', (amount, category, description, date))
            
            self.conn.commit()
            
            # Clear inputs
            self.amount_input.text = ''
            self.category_spinner.text = 'Select Category'
            self.description_input.text = ''
            self.date_input.text = datetime.now().strftime('%Y-%m-%d')
            
            self.update_balance()
            self.show_popup('Success', f'Expense of ${amount:.2f} added successfully')
            
        except ValueError:
            self.show_popup('Error', 'Please enter valid amount and date (YYYY-MM-DD)')
    
    def update_balance(self, *args):
        """Update balance display"""
        cursor = self.conn.cursor()
        
        # Get current month salary
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('SELECT amount FROM salary WHERE month = ?', (current_month,))
        salary_result = cursor.fetchone()
        salary = salary_result[0] if salary_result else 0
        
        # Get total expenses for current month
        cursor.execute('''
            SELECT SUM(amount) FROM expenses 
            WHERE date LIKE ?
        ''', (f'{current_month}%',))
        expenses_result = cursor.fetchone()
        total_expenses = expenses_result[0] if expenses_result[0] else 0
        
        balance = salary - total_expenses
        self.balance_label.text = f'Balance: ${balance:.2f}\n(Salary: ${salary:.2f} - Expenses: ${total_expenses:.2f})'
    
    def view_expenses(self, instance):
        """View all expenses in a popup"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT amount, category, description, date 
            FROM expenses 
            ORDER BY date DESC
            LIMIT 50
        ''')
        expenses = cursor.fetchall()
        
        content = BoxLayout(orientation='vertical', spacing=10)
        
        if expenses:
            scroll = ScrollView()
            expenses_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
            expenses_layout.bind(minimum_height=expenses_layout.setter('height'))
            
            for expense in expenses:
                expense_text = f'${expense[0]:.2f} - {expense[1]} - {expense[3]}\n{expense[2]}'
                expense_label = Label(text=expense_text, size_hint_y=None, height=70,
                                    text_size=(None, None), halign='left', font_size=14)
                expenses_layout.add_widget(expense_label)
            
            scroll.add_widget(expenses_layout)
            content.add_widget(scroll)
        else:
            content.add_widget(Label(text='No expenses found', font_size=16))
        
        close_btn = Button(text='Close', size_hint_y=None, height=60, font_size=16)
        content.add_widget(close_btn)
        
        popup = Popup(title='Recent Expenses', content=content, size_hint=(0.95, 0.8))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def export_to_excel(self, instance):
        """Export expenses to Excel file"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT amount, category, description, date, timestamp
                FROM expenses 
                ORDER BY date DESC
            ''')
            expenses = cursor.fetchall()
            
            if not expenses:
                self.show_popup('Error', 'No expenses to export')
                return
            
            # Create DataFrame
            df = pd.DataFrame(expenses, columns=['Amount', 'Category', 'Description', 'Date', 'Timestamp'])
            
            # Create filename with current date
            export_dir = self.get_export_directory()
            filename = os.path.join(export_dir, f'expenses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
            
            # Export to Excel
            df.to_excel(filename, index=False)
            
            self.show_popup('Success', f'Expenses exported to:\n{filename}')
            
        except Exception as e:
            self.show_popup('Error', f'Export failed: {str(e)}')
    
    def show_statistics(self, instance):
        """Show comprehensive statistics"""
        cursor = self.conn.cursor()
        
        # Monthly totals
        cursor.execute('''
            SELECT strftime('%Y-%m', date) as month, SUM(amount) as total
            FROM expenses
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        ''')
        monthly_results = cursor.fetchall()
        
        # Category totals
        cursor.execute('''
            SELECT category, SUM(amount) as total, COUNT(*) as count
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
        ''')
        category_results = cursor.fetchall()
        
        text = 'EXPENSE STATISTICS\n\n'
        
        if monthly_results:
            text += 'Monthly Expenses:\n'
            for month, total in monthly_results:
                text += f'{month}: ${total:.2f}\n'
            text += '\n'
        
        if category_results:
            text += 'Category Breakdown:\n'
            for category, total, count in category_results:
                text += f'{category}: ${total:.2f} ({count}x)\n'
        
        if not monthly_results and not category_results:
            text += 'No expenses found'
        
        self.show_popup('Statistics', text)
    
    def show_popup(self, title, message):
        """Show popup message"""
        content = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        label = Label(text=message, font_size=16, text_size=(None, None))
        content.add_widget(label)
        
        close_btn = Button(text='Close', size_hint_y=None, height=60, font_size=16)
        content.add_widget(close_btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.9, 0.7))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def on_pause(self):
        """Handle app pause (Android)"""
        return True
    
    def on_resume(self):
        """Handle app resume (Android)"""
        pass

if __name__ == '__main__':
    ExpenseTrackerApp().run()