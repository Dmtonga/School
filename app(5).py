#===========================================================
#Below are Python libraries sometimes called (modules). They are a collection of ready-made 
#code that you can use instead of writing everything yourself.
#===========================================================
import streamlit as st
import pandas as pd
import pyodbc
import hashlib

# ============================================================
# The Below three lines define the SQL Server database
#  connection information for the application
# AGRIAUCTION - APPLICATION
# ============================================================

SERVER = "localhost"
DATABASE = "AgriAuctionDB"
DRIVER = "ODBC Driver 17 for SQL Server"

#==========================================================================
# Below is a functions which is connecting the python Streamlit application
# to my SQL Server and performing database operations.
#==========================================================================
def connect():
    return pyodbc.connect(
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )


def read_sql(sql, params=()):
    conn = connect()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def execute_sql(sql, params=()):
    conn = connect()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def execute_procedure(sql, params=()):
    conn = connect()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
    finally:
        conn.close()

#===================================================================
# This line take a user's Password and convert it into a hash value.
#===================================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

#=============================================================
# This Line Check if a user is allowed to login to the system
#=============================================================

def login(username, password):
    password_hash = hash_password(password)

    sql = """
        SELECT UserID, Username, FullName, UserRole
        FROM dbo.Users
        WHERE Username = ?
          AND UserPassword = ?
          AND IsActive = 1
    """

    df = read_sql(sql, (username, password_hash))

    #===========================================================
    # The SQL setup script may contain the simple classroom
    # passwords. This fallback lets the original sample accounts
    # work until they are changed to hashed passwords.
    #===========================================================
    if df.empty:
        sql2 = """
            SELECT UserID, Username, FullName, UserRole
            FROM dbo.Users
            WHERE Username = ?
              AND UserPassword = ?
              AND IsActive = 1
        """
        df = read_sql(sql2, (username, password))

    if not df.empty:
        return df.iloc[0].to_dict()

    return None
#===========================================================================================
# This function creates the login screen that the user sees the moment the application opens.
#===========================================================================================

def show_login():
    st.title("AgriAuction Management System")
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            user = login(username, password)

            if user:
                st.session_state.user = user
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        except Exception as e:
            st.error(f"Database error: {e}")

#============================================================================
# This function creates the appliction's main dashboard
#============================================================================
def dashboard():
    st.header("Dashboard")

    farmers = read_sql("SELECT COUNT(*) AS Total FROM dbo.Farmer").iloc[0, 0]
    buyers = read_sql("SELECT COUNT(*) AS Total FROM dbo.Buyer").iloc[0, 0]
    produce = read_sql("SELECT COUNT(*) AS Total FROM dbo.Produce").iloc[0, 0]
    bids = read_sql("SELECT COUNT(*) AS Total FROM dbo.Bid").iloc[0, 0]
    sales = read_sql("SELECT COUNT(*) AS Total FROM dbo.Sale").iloc[0, 0]
    payments = read_sql("SELECT COUNT(*) AS Total FROM dbo.Payment").iloc[0, 0]
    collections = read_sql("SELECT COUNT(*) AS Total FROM dbo.Collection").iloc[0, 0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Farmers", farmers)
    c2.metric("Buyers", buyers)
    c3.metric("Produce", produce)
    c4.metric("Bids", bids)

    c5, c6, c7 = st.columns(3)
    c5.metric("Sales", sales)
    c6.metric("Payments", payments)
    c7.metric("Collections", collections)

    st.subheader("Open Produce")
    st.dataframe(
        read_sql("SELECT * FROM dbo.vw_AvailableProduce"),
        use_container_width=True
    )

#============================================================================================
# This section create the farmer management this is where all
# all the Farmer's create, read, unpate and delete happen
#=============================================================================================

def farmers():
    st.header("Farmers")

    tab1, tab2, tab3 = st.tabs(["Add Farmer", "View / Edit", "Delete"])

    with tab1:
        first = st.text_input("First Name")
        last = st.text_input("Last Name")
        phone = st.text_input("Phone")
        location = st.text_input("Location")

        if st.button("Add Farmer"):
            try:
                execute_procedure(
                    "EXEC dbo.usp_AddFarmer ?, ?, ?, ?",
                    (first, last, phone, location)
                )
                st.success("Farmer added.")
            except Exception as e:
                st.error(str(e))

    with tab2:
        df = read_sql("SELECT * FROM dbo.Farmer")
        st.dataframe(df, use_container_width=True)

        farmer_id = st.number_input("Farmer ID", min_value=1, step=1)
        new_first = st.text_input("New First Name")
        new_last = st.text_input("New Last Name")
        new_phone = st.text_input("New Phone")
        new_location = st.text_input("New Location")

        if st.button("Update Farmer"):
            try:
                execute_sql(
                    """
                    UPDATE dbo.Farmer
                    SET FirstName=?, LastName=?, Phone=?, Location=?
                    WHERE FarmerID=?
                    """,
                    (new_first, new_last, new_phone, new_location, farmer_id)
                )
                st.success("Farmer updated.")
            except Exception as e:
                st.error(str(e))

    with tab3:
        delete_id = st.number_input(
            "Farmer ID to delete", min_value=1, step=1, key="delete_farmer"
        )

        if st.button("Delete Farmer"):
            try:
                execute_sql(
                    "DELETE FROM dbo.Farmer WHERE FarmerID=?",
                    (delete_id,)
                )
                st.success("Farmer deleted.")
            except Exception as e:
                st.error("Farmer cannot be deleted if produce still belongs to the farmer.")

#=================================================================
# This section create the buyer management page this is where all
# all the Buyer's create, read, unpate and delete happen
#=================================================================
def buyers():
    st.header("Buyers")

    tab1, tab2, tab3 = st.tabs(["Add Buyer", "View / Edit", "Delete"])

    with tab1:
        name = st.text_input("Business Name")
        contact = st.text_input("Contact Person")
        phone = st.text_input("Phone")

        if st.button("Add Buyer"):
            try:
                execute_sql(
                    """
                    INSERT INTO dbo.Buyer
                    (BusinessName, ContactPerson, Phone)
                    VALUES (?, ?, ?)
                    """,
                    (name, contact, phone)
                )
                st.success("Buyer added.")
            except Exception as e:
                st.error(str(e))

    with tab2:
        st.dataframe(
            read_sql("SELECT * FROM dbo.Buyer"),
            use_container_width=True
        )

        buyer_id = st.number_input("Buyer ID", min_value=1, step=1)
        new_name = st.text_input("New Business Name")
        new_contact = st.text_input("New Contact Person")
        new_phone = st.text_input("New Phone")

        if st.button("Update Buyer"):
            try:
                execute_sql(
                    """
                    UPDATE dbo.Buyer
                    SET BusinessName=?, ContactPerson=?, Phone=?
                    WHERE BuyerID=?
                    """,
                    (new_name, new_contact, new_phone, buyer_id)
                )
                st.success("Buyer updated.")
            except Exception as e:
                st.error(str(e))

    with tab3:
        delete_id = st.number_input(
            "Buyer ID to delete", min_value=1, step=1, key="delete_buyer"
        )

        if st.button("Delete Buyer"):
            try:
                execute_sql(
                    "DELETE FROM dbo.Buyer WHERE BuyerID=?",
                    (delete_id,)
                )
                st.success("Buyer deleted.")
            except Exception:
                st.error("Buyer cannot be deleted because the buyer has bids or sales.")

#==========================================================================================
# This section create the Produce management page this is where all
# all the Produce's create, read, unpate and delete happen
#==========================================================================================
def produce():
    st.header("Produce")

    tab1, tab2, tab3 = st.tabs(["Add Produce", "View / Edit", "Delete"])

    farmers_df = read_sql(
        "SELECT FarmerID, FirstName + ' ' + LastName AS Farmer FROM dbo.Farmer"
    )

    with tab1:
        if farmers_df.empty:
            st.warning("Add a farmer first.")
            return

        farmer_id = st.selectbox(
            "Farmer",
            farmers_df["FarmerID"].tolist(),
            format_func=lambda x: farmers_df.loc[
                farmers_df["FarmerID"] == x, "Farmer"
            ].iloc[0]
        )

        name = st.text_input("Produce Name")
        quantity = st.number_input("Quantity", min_value=0.01, step=1.0)
        unit = st.text_input("Unit", value="bags")
        minimum = st.number_input("Minimum Price", min_value=0.0, step=10.0)
        auction_end = st.datetime_input("Auction End")

        if st.button("Add Produce"):
            try:
                execute_sql(
                    """
                    INSERT INTO dbo.Produce
                    (FarmerID, ProduceName, Quantity, Unit, MinimumPrice, AuctionEnd)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (farmer_id, name, quantity, unit, minimum, auction_end)
                )
                st.success("Produce added.")
            except Exception as e:
                st.error(str(e))

    with tab2:
        st.dataframe(
            read_sql("SELECT * FROM dbo.Produce"),
            use_container_width=True
        )

        produce_id = st.number_input(
            "Produce ID", min_value=1, step=1, key="edit_produce"
        )
        new_name = st.text_input("New Produce Name")
        new_quantity = st.number_input(
            "New Quantity", min_value=0.01, step=1.0, key="new_qty"
        )
        new_unit = st.text_input("New Unit", key="new_unit")
        new_minimum = st.number_input(
            "New Minimum Price", min_value=0.0, step=10.0, key="new_min"
        )

        if st.button("Update Produce"):
            try:
                execute_sql(
                    """
                    UPDATE dbo.Produce
                    SET ProduceName=?, Quantity=?, Unit=?, MinimumPrice=?
                    WHERE ProduceID=? AND Status='OPEN'
                    """,
                    (new_name, new_quantity, new_unit, new_minimum, produce_id)
                )
                st.success("Produce updated.")
            except Exception as e:
                st.error(str(e))

    with tab3:
        delete_id = st.number_input(
            "Produce ID to delete", min_value=1, step=1, key="delete_produce"
        )

        if st.button("Delete Produce"):
            try:
                execute_sql(
                    "DELETE FROM dbo.Produce WHERE ProduceID=? AND Status='OPEN'",
                    (delete_id,)
                )
                st.success("Produce deleted.")
            except Exception:
                st.error("Produce cannot be deleted because it has bids or a sale.")

#===============================================================================
# This function creates the Bidding section of the appliction. 
# It allows a buyer to select available produce, and enter a bid amount, place the
# bid, and then view all bids that have been made.
#===============================================================================
def bids():
    st.header("Bidding")

    produce_df = read_sql("""
        SELECT ProduceID, ProduceName, MinimumPrice
        FROM dbo.Produce
        WHERE Status='OPEN'
          AND AuctionEnd >= SYSDATETIME()
    """)

    buyers_df = read_sql("""
        SELECT BuyerID, BusinessName
        FROM dbo.Buyer
    """)

    if produce_df.empty:
        st.info("There is no open produce available for bidding.")
        return

    if buyers_df.empty:
        st.warning("Add a buyer first.")
        return

    produce_id = st.selectbox(
        "Produce",
        produce_df["ProduceID"].tolist(),
        format_func=lambda x: produce_df.loc[
            produce_df["ProduceID"] == x, "ProduceName"
        ].iloc[0]
    )

    buyer_id = st.selectbox(
        "Buyer",
        buyers_df["BuyerID"].tolist(),
        format_func=lambda x: buyers_df.loc[
            buyers_df["BuyerID"] == x, "BusinessName"
        ].iloc[0]
    )

    amount = st.number_input("Bid Amount", min_value=0.01, step=10.0)

    if st.button("Place Bid"):
        try:
            execute_procedure(
                "EXEC dbo.usp_PlaceBid ?, ?, ?",
                (produce_id, buyer_id, amount)
            )
            st.success("Bid placed successfully.")
        except Exception as e:
            st.error(str(e))

    st.subheader("All Bids")
    st.dataframe(
        read_sql("""
            SELECT
                b.BidID,
                p.ProduceName,
                bu.BusinessName AS Buyer,
                b.BidAmount,
                b.BidDateTime,
                b.BidStatus
            FROM dbo.Bid b
            JOIN dbo.Produce p ON b.ProduceID=p.ProduceID
            JOIN dbo.Buyer bu ON b.BuyerID=bu.BuyerID
            ORDER BY b.BidDateTime DESC
        """),
        use_container_width=True
    )
#===============================================================================
# This Function closes the auction after the time set for the to set has reached
#===============================================================================

def close_auction():
    st.header("Close Auction")

    df = read_sql("""
        SELECT ProduceID, ProduceName, AuctionEnd
        FROM dbo.Produce
        WHERE Status='OPEN'
          AND AuctionEnd <= SYSDATETIME()
    """)

    if df.empty:
        st.info("There are no auctions ready to close.")
        return

    produce_id = st.selectbox(
        "Auction to close",
        df["ProduceID"].tolist(),
        format_func=lambda x: df.loc[
            df["ProduceID"] == x, "ProduceName"
        ].iloc[0]
    )

    if st.button("Close Auction"):
        try:
            execute_procedure(
                "EXEC dbo.usp_CloseAuction ?",
                (produce_id,)
            )

            result = read_sql("""
                SELECT TOP 1
                    s.SaleID,
                    p.ProduceName,
                    b.BusinessName AS Winner,
                    s.WinningBid,
                    s.SaleDate
                FROM dbo.Sale s
                JOIN dbo.Produce p ON s.ProduceID=p.ProduceID
                JOIN dbo.Buyer b ON s.BuyerID=b.BuyerID
                WHERE s.ProduceID=?
                ORDER BY s.SaleID DESC
            """, (produce_id,))

            if not result.empty:
                st.success("Auction closed and sale created for the winning buyer.")
                st.dataframe(result, use_container_width=True)
            else:
                st.warning("Auction closed without a winning bid.")

        except Exception as e:
            st.error(str(e))

#======================================================================================
# This function creates a sale once the Auction has been colesd and if there is a buyer
#======================================================================================
def sales():
    st.header("Sales")

    st.dataframe(
        read_sql("""
            SELECT *
            FROM dbo.vw_AuctionResults
            ORDER BY SaleDate DESC
        """),
        use_container_width=True
    )

#==========================================================
# This function creates the Payments page of auction system
#==========================================================
def payments():
    st.header("Payments")

    sales_df = read_sql("""
        SELECT
            s.SaleID,
            p.ProduceName,
            b.BusinessName AS Buyer,
            s.WinningBid,
            ISNULL(SUM(pay.Amount), 0) AS AmountPaid,
            s.WinningBid - ISNULL(SUM(pay.Amount), 0) AS Balance
        FROM dbo.Sale s
        JOIN dbo.Produce p ON s.ProduceID=p.ProduceID
        JOIN dbo.Buyer b ON s.BuyerID=b.BuyerID
        LEFT JOIN dbo.Payment pay ON s.SaleID=pay.SaleID
        GROUP BY s.SaleID, p.ProduceName, b.BusinessName, s.WinningBid
        ORDER BY s.SaleID DESC
    """)

    st.dataframe(sales_df, use_container_width=True)

    if sales_df.empty:
        st.info("There are no sales to receive payment for.")
        return

    sale_id = st.selectbox(
        "Sale",
        sales_df["SaleID"].tolist(),
        format_func=lambda x: f"Sale {x} - {sales_df.loc[sales_df['SaleID']==x, 'Buyer'].iloc[0]}"
    )

    selected = sales_df[sales_df["SaleID"] == sale_id].iloc[0]
    st.write(f"Sale amount: K {selected['WinningBid']:,.2f}")
    st.write(f"Already paid: K {selected['AmountPaid']:,.2f}")
    st.write(f"Balance: K {selected['Balance']:,.2f}")

    amount = st.number_input(
        "Payment Amount", min_value=0.01, step=10.0
    )
    method = st.selectbox(
        "Payment Method",
        ["Cash", "Bank Transfer", "Mobile Money"]
    )

    if st.button("Record Payment"):
        try:
            execute_procedure(
                "EXEC dbo.usp_RecordPayment ?, ?, ?",
                (sale_id, amount, method)
            )
            st.success("Payment recorded.")
        except Exception as e:
            st.error(str(e))

#================================================================================================
# This Function creates the Collections. this is used to track how much produce was collected by 
# the buyer and how much is still remaining.
#================================================================================================
def collections():
    st.header("Collections")

    sales_df = read_sql("""
        SELECT
            s.SaleID,
            p.ProduceName,
            b.BusinessName AS Buyer,
            p.Quantity AS TotalQuantity,
            ISNULL(SUM(c.QuantityCollected), 0) AS Collected,
            p.Quantity - ISNULL(SUM(c.QuantityCollected), 0) AS Remaining
        FROM dbo.Sale s
        JOIN dbo.Produce p ON s.ProduceID=p.ProduceID
        JOIN dbo.Buyer b ON s.BuyerID=b.BuyerID
        LEFT JOIN dbo.Collection c ON s.SaleID=c.SaleID
        GROUP BY s.SaleID, p.ProduceName, b.BusinessName, p.Quantity
        ORDER BY s.SaleID DESC
    """)

    st.dataframe(sales_df, use_container_width=True)

    if sales_df.empty:
        st.info("There are no sales ready for collection.")
        return

    sale_id = st.selectbox(
        "Sale",
        sales_df["SaleID"].tolist(),
        format_func=lambda x: f"Sale {x} - {sales_df.loc[sales_df['SaleID']==x, 'Buyer'].iloc[0]}"
    )

    selected = sales_df[sales_df["SaleID"] == sale_id].iloc[0]
    st.write(f"Total quantity: {selected['TotalQuantity']}")
    st.write(f"Already collected: {selected['Collected']}")
    st.write(f"Remaining: {selected['Remaining']}")

    quantity = st.number_input(
        "Quantity Collected", min_value=0.01, step=1.0
    )
    collected_by = st.text_input("Collected By")

    if st.button("Record Collection"):
        try:
            execute_procedure(
                "EXEC dbo.usp_RecordCollection ?, ?, ?",
                (sale_id, quantity, collected_by)
            )
            st.success("Collection recorded.")
        except Exception as e:
            st.error(str(e))

#==============================================================
# The Report function is the Reports Module of your AgriAuction 
# Management System. It displays three database reports through 
# Streamlit web application.
#==============================================================

def reports():
    st.header("Reports")

    st.subheader("Auction Results")
    st.dataframe(
        read_sql("SELECT * FROM dbo.vw_AuctionResults"),
        use_container_width=True
    )

    st.subheader("Sales and Payments")
    st.dataframe(
        read_sql("SELECT * FROM dbo.vw_SalesPayments"),
        use_container_width=True
    )

    st.subheader("Collections")
    st.dataframe(
        read_sql("SELECT * FROM dbo.vw_Collections"),
        use_container_width=True
    )

#========================================================
# The User Management function controls the users who are
# allowed to use the AgriAuction Management System
#========================================================
def user_management():
    st.header("User Management")

    users = read_sql("""
        SELECT UserID, Username, FullName, UserRole, IsActive
        FROM dbo.Users
        ORDER BY UserID
    """)
    st.dataframe(users, use_container_width=True)

    st.subheader("Create New User")

    username = st.text_input("Username", key="new_username")
    fullname = st.text_input("Full Name", key="new_fullname")
    password = st.text_input("Password", type="password", key="new_password")
    role = st.selectbox(
        "Role",
        ["ADMIN", "DEPOT", "AUCTION", "FINANCE"],
        key="new_role"
    )

    if st.button("Create User"):
        if not username or not fullname or not password:
            st.warning("Enter username, full name and password.")
            return

        try:
            password_hash = hash_password(password)

            execute_sql(
                """
                INSERT INTO dbo.Users
                (Username, UserPassword, FullName, UserRole, IsActive)
                VALUES (?, ?, ?, ?, 1)
                """,
                (username, password_hash, fullname, role)
            )

            st.success("User created successfully.")
        except Exception as e:
            st.error(f"Could not create user: {e}")

    st.subheader("Deactivate User")

    user_id = st.number_input(
        "User ID", min_value=1, step=1, key="deactivate_user"
    )

    if st.button("Deactivate User"):
        try:
            execute_sql(
                "UPDATE dbo.Users SET IsActive=0 WHERE UserID=?",
                (user_id,)
            )
            st.success("User deactivated.")
        except Exception as e:
            st.error(str(e))

#=========================================================
#This is the main function, it controls the
# AgriAuction application. It controls login, user roles,
# the sidebar menu, navigation between modules, and error
# handling.
#=========================================================
def main():
    st.set_page_config(
        page_title="AgriAuction",
        layout="wide"
    )

    if "user" not in st.session_state:
        show_login()
        return

    user = st.session_state.user

    st.sidebar.title("AgriAuction")
    st.sidebar.write(f"User: {user['FullName']}")
    st.sidebar.write(f"Role: {user['UserRole']}")

    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.rerun()

    role = user["UserRole"]

    if role == "ADMIN":
        menu = st.sidebar.radio(
            "Menu",
            [
                "Dashboard",
                "Farmers",
                "Buyers",
                "Produce",
                "Bids",
                "Close Auction",
                "Sales",
                "Payments",
                "Collections",
                "Reports",
                "User Management"
            ]
        )

    elif role == "DEPOT":
        menu = st.sidebar.radio(
            "Menu",
            ["Dashboard", "Farmers", "Produce"]
        )

    elif role == "AUCTION":
        menu = st.sidebar.radio(
            "Menu",
            ["Dashboard", "Buyers", "Bids", "Close Auction", "Sales"]
        )

    else:
        menu = st.sidebar.radio(
            "Menu",
            ["Dashboard", "Sales", "Payments", "Collections", "Reports"]
        )

    try:
        if menu == "Dashboard":
            dashboard()
        elif menu == "Farmers":
            farmers()
        elif menu == "Buyers":
            buyers()
        elif menu == "Produce":
            produce()
        elif menu == "Bids":
            bids()
        elif menu == "Close Auction":
            close_auction()
        elif menu == "Sales":
            sales()
        elif menu == "Payments":
            payments()
        elif menu == "Collections":
            collections()
        elif menu == "Reports":
            reports()
        elif menu == "User Management":
            user_management()

    except Exception as e:
        st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
