/* ============================================================
   This SQL script REBUILDS the ArigiAution Database.
   It deletes the old AgriAuctionDB and creates a clean copy.
   ============================================================ */

USE master;
GO

IF DB_ID('AgriAuctionDB') IS NOT NULL
BEGIN
    ALTER DATABASE AgriAuctionDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE AgriAuctionDB;
END;
GO

CREATE DATABASE AgriAuctionDB;
GO

USE AgriAuctionDB;
GO

/* =========================
   1. This SQL Code Creats the user for storing user information
   ========================= */
CREATE TABLE dbo.Users
(
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    Username VARCHAR(50) NOT NULL UNIQUE,
    UserPassword VARCHAR(100) NOT NULL,
    FullName VARCHAR(100) NOT NULL,
    UserRole VARCHAR(20) NOT NULL
        CHECK (UserRole IN ('ADMIN','DEPOT','AUCTION','FINANCE')),
    IsActive BIT NOT NULL DEFAULT 1
);
GO

/* =========================
   2. This SQL Code Creats the Table for storing Farmers information
   ========================= */
CREATE TABLE dbo.Farmer
(
    FarmerID INT IDENTITY(1,1) PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Phone VARCHAR(30) NULL,
    Location VARCHAR(100) NULL
);
GO

/* =========================
   3. This SQL Code Creats the Table for storing Buyers information
   ========================= */
CREATE TABLE dbo.Buyer
(
    BuyerID INT IDENTITY(1,1) PRIMARY KEY,
    BusinessName VARCHAR(100) NOT NULL,
    ContactPerson VARCHAR(100) NULL,
    Phone VARCHAR(30) NULL
);
GO

/* =========================
   4. This SQL Code Creats the Table for storing Produce information
   ========================= */
CREATE TABLE dbo.Produce
(
    ProduceID INT IDENTITY(1,1) PRIMARY KEY,
    FarmerID INT NOT NULL,
    ProduceName VARCHAR(100) NOT NULL,
    Quantity DECIMAL(12,2) NOT NULL CHECK (Quantity > 0),
    Unit VARCHAR(20) NOT NULL,
    MinimumPrice DECIMAL(12,2) NOT NULL CHECK (MinimumPrice >= 0),
    AuctionEnd DATETIME2 NOT NULL,
    Status VARCHAR(20) NOT NULL DEFAULT 'OPEN'
        CHECK (Status IN ('OPEN','SOLD','UNSOLD')),
    CONSTRAINT FK_Produce_Farmer
        FOREIGN KEY (FarmerID) REFERENCES dbo.Farmer(FarmerID)
);
GO

/* =========================
   5. This SQL Code Creats the Table for storing Bids information
   ========================= */
CREATE TABLE dbo.Bid
(
    BidID INT IDENTITY(1,1) PRIMARY KEY,
    ProduceID INT NOT NULL,
    BuyerID INT NOT NULL,
    BidAmount DECIMAL(12,2) NOT NULL CHECK (BidAmount > 0),
    BidDateTime DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    BidStatus VARCHAR(20) NOT NULL DEFAULT 'VALID'
        CHECK (BidStatus IN ('VALID','WINNER','REJECTED')),
    CONSTRAINT FK_Bid_Produce
        FOREIGN KEY (ProduceID) REFERENCES dbo.Produce(ProduceID),
    CONSTRAINT FK_Bid_Buyer
        FOREIGN KEY (BuyerID) REFERENCES dbo.Buyer(BuyerID)
);
GO

/* =========================
   6. This SQL Code Creats the Table for storing Sales information
   ========================= */
CREATE TABLE dbo.Sale
(
    SaleID INT IDENTITY(1,1) PRIMARY KEY,
    ProduceID INT NOT NULL UNIQUE,
    BuyerID INT NOT NULL,
    WinningBid DECIMAL(12,2) NOT NULL,
    SaleDate DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_Sale_Produce
        FOREIGN KEY (ProduceID) REFERENCES dbo.Produce(ProduceID),
    CONSTRAINT FK_Sale_Buyer
        FOREIGN KEY (BuyerID) REFERENCES dbo.Buyer(BuyerID)
);
GO


/* =========================
   7. This SQL Code Creats the Table for storing Payment information
   ========================= */
CREATE TABLE dbo.Payment
(
    PaymentID INT IDENTITY(1,1) PRIMARY KEY,
    SaleID INT NOT NULL,
    Amount DECIMAL(12,2) NOT NULL CHECK (Amount > 0),
    PaymentDate DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    PaymentMethod VARCHAR(30) NOT NULL,
    CONSTRAINT FK_Payment_Sale
        FOREIGN KEY (SaleID) REFERENCES dbo.Sale(SaleID)
);
GO

/* =========================
   8. This SQL Code Creats the Table for storing Collections information
   ========================= */
CREATE TABLE dbo.Collection
(
    CollectionID INT IDENTITY(1,1) PRIMARY KEY,
    SaleID INT NOT NULL,
    QuantityCollected DECIMAL(12,2) NOT NULL CHECK (QuantityCollected > 0),
    CollectionDate DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CollectedBy VARCHAR(100) NOT NULL,
    CONSTRAINT FK_Collection_Sale
        FOREIGN KEY (SaleID) REFERENCES dbo.Sale(SaleID)
);
GO

/* =========================
   This SQL Code inserts default user information for the first time usage of the system
   ========================= */
INSERT INTO dbo.Users (Username, UserPassword, FullName, UserRole)
VALUES
('admin',    'admin123',    'System Administrator', 'ADMIN'),
('depot1',   'depot123',    'Depot Officer',        'DEPOT'),
('auction1', 'auction123',  'Auction Officer',      'AUCTION'),
('finance1', 'finance123',  'Finance Officer',      'FINANCE');
GO

/* =========================
   This SQL Code inserts sample data into the table Farmer
   ========================= */
INSERT INTO dbo.Farmer (FirstName, LastName, Phone, Location)
VALUES
('John', 'Banda', '0971111111', 'Lusaka'),
('Mary', 'Phiri', '0972222222', 'Chongwe');
GO

/* =========================
   This SQL Code inserts sample data into the table Buyer
   ========================= */
INSERT INTO dbo.Buyer (BusinessName, ContactPerson, Phone)
VALUES
('Zambezi Foods', 'Peter Mwansa', '0961111111'),
('Farm Fresh Ltd', 'Grace Tembo', '0962222222');
GO

/* ============================================================
   This SQL Code Creates a view that shows all availbe Produces
   ============================================================ */
CREATE VIEW dbo.vw_AvailableProduce
AS
SELECT
    p.ProduceID,
    CONCAT(f.FirstName, ' ', f.LastName) AS Farmer,
    p.ProduceName,
    p.Quantity,
    p.Unit,
    p.MinimumPrice,
    p.AuctionEnd,
    p.Status
FROM dbo.Produce AS p
INNER JOIN dbo.Farmer AS f
    ON p.FarmerID = f.FarmerID
WHERE p.Status = 'OPEN';
GO

/* ============================================================
   This SQL Code Creates a view that shows all completed Auctions
   ============================================================ */
CREATE VIEW dbo.vw_AuctionResults
AS
SELECT
    s.SaleID,
    p.ProduceName,
    CONCAT(f.FirstName, ' ', f.LastName) AS Farmer,
    b.BusinessName AS Buyer,
    s.WinningBid,
    s.SaleDate
FROM dbo.Sale AS s
INNER JOIN dbo.Produce AS p
    ON s.ProduceID = p.ProduceID
INNER JOIN dbo.Farmer AS f
    ON p.FarmerID = f.FarmerID
INNER JOIN dbo.Buyer AS b
    ON s.BuyerID = b.BuyerID;
GO


/* ============================================================
   This SQL Code Creates a view that shows all payment status for Auction sale
   ============================================================ */
CREATE VIEW dbo.vw_SalesPayments
AS
SELECT
    s.SaleID,
    p.ProduceName,
    b.BusinessName AS Buyer,
    s.WinningBid AS SaleAmount,
    ISNULL(SUM(pay.Amount), 0) AS AmountPaid,
    s.WinningBid - ISNULL(SUM(pay.Amount), 0) AS Balance
FROM dbo.Sale AS s
INNER JOIN dbo.Produce AS p
    ON s.ProduceID = p.ProduceID
INNER JOIN dbo.Buyer AS b
    ON s.BuyerID = b.BuyerID
LEFT JOIN dbo.Payment AS pay
    ON s.SaleID = pay.SaleID
GROUP BY
    s.SaleID, p.ProduceName, b.BusinessName, s.WinningBid;
GO

/* ============================================================
   This SQL Code Creates a view that shows the collection record for every produce sold
   ============================================================ */
CREATE VIEW dbo.vw_Collections
AS
SELECT
    c.CollectionID,
    c.SaleID,
    p.ProduceName,
    b.BusinessName AS Buyer,
    p.Quantity AS TotalQuantity,
    c.QuantityCollected,
    c.CollectionDate,
    c.CollectedBy
FROM dbo.Collection AS c
INNER JOIN dbo.Sale AS s
    ON c.SaleID = s.SaleID
INNER JOIN dbo.Produce AS p
    ON s.ProduceID = p.ProduceID
INNER JOIN dbo.Buyer AS b
    ON s.BuyerID = b.BuyerID;
GO

/* ============================================================
   This is a user defined procedure, used as a simple reusable sql for add a new farmer into the table Farmer
   ============================================================ */
CREATE PROCEDURE dbo.usp_AddFarmer
    @FirstName VARCHAR(50),
    @LastName VARCHAR(50),
    @Phone VARCHAR(30),
    @Location VARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.Farmer
        (FirstName, LastName, Phone, Location)
    VALUES
        (@FirstName, @LastName, @Phone, @Location);
END;
GO

/* ============================================================
   This is a user defined procedure, used as a simple reusable sql for alowing a farmer to place a bid on a Produce
   ============================================================ */
CREATE PROCEDURE dbo.usp_PlaceBid
    @ProduceID INT,
    @BuyerID INT,
    @BidAmount DECIMAL(12,2)
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Produce
        WHERE ProduceID = @ProduceID
          AND Status = 'OPEN'
          AND AuctionEnd >= SYSDATETIME()
          AND @BidAmount >= MinimumPrice
    )
    BEGIN
        RAISERROR('Bid is not allowed. Check the auction, price and produce.',16,1);
        RETURN;
    END;

    INSERT INTO dbo.Bid
        (ProduceID, BuyerID, BidAmount)
    VALUES
        (@ProduceID, @BuyerID, @BidAmount);
END;
GO

/* ============================================================
   This is a user defined procedure, used as a simple reusable sql for closing the bid was bidding time closes
   ============================================================ */
CREATE PROCEDURE dbo.usp_CloseAuction
    @ProduceID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
        BEGIN TRANSACTION;

        DECLARE @Status VARCHAR(20);
        DECLARE @EndTime DATETIME2;

        SELECT
            @Status = Status,
            @EndTime = AuctionEnd
        FROM dbo.Produce WITH (UPDLOCK, HOLDLOCK)
        WHERE ProduceID = @ProduceID;

        IF @Status IS NULL
            THROW 50001, 'Produce item was not found.', 1;

        IF @Status <> 'OPEN'
            THROW 50002, 'This auction is already closed.', 1;

        IF @EndTime > SYSDATETIME()
            THROW 50003, 'The auction has not ended yet.', 1;

        DECLARE @BidID INT;
        DECLARE @BuyerID INT;
        DECLARE @Amount DECIMAL(12,2);

        SELECT TOP 1
            @BidID = BidID,
            @BuyerID = BuyerID,
            @Amount = BidAmount
        FROM dbo.Bid WITH (UPDLOCK, HOLDLOCK)
        WHERE ProduceID = @ProduceID
          AND BidStatus = 'VALID'
        ORDER BY BidAmount DESC, BidDateTime ASC;

        IF @BidID IS NULL
        BEGIN
            UPDATE dbo.Produce
            SET Status = 'UNSOLD'
            WHERE ProduceID = @ProduceID;

            COMMIT TRANSACTION;
            RETURN;
        END;

        UPDATE dbo.Bid
        SET BidStatus = 'WINNER'
        WHERE BidID = @BidID;

        UPDATE dbo.Bid
        SET BidStatus = 'REJECTED'
        WHERE ProduceID = @ProduceID
          AND BidID <> @BidID
          AND BidStatus = 'VALID';

        INSERT INTO dbo.Sale
            (ProduceID, BuyerID, WinningBid)
        VALUES
            (@ProduceID, @BuyerID, @Amount);

        UPDATE dbo.Produce
        SET Status = 'SOLD'
        WHERE ProduceID = @ProduceID;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO


/* ============================================================
   This is a user defined procedure, used as a simple reusable sql for recording a payment against a sale 
   ============================================================ */
CREATE PROCEDURE dbo.usp_RecordPayment
    @SaleID INT,
    @Amount DECIMAL(12,2),
    @PaymentMethod VARCHAR(30)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @SaleAmount DECIMAL(12,2);
        DECLARE @Paid DECIMAL(12,2);

        SELECT @SaleAmount = WinningBid
        FROM dbo.Sale
        WHERE SaleID = @SaleID;

        IF @SaleAmount IS NULL
            THROW 50004, 'Sale was not found.', 1;

        SELECT @Paid = ISNULL(SUM(Amount), 0)
        FROM dbo.Payment
        WHERE SaleID = @SaleID;

        IF @Amount <= 0
            THROW 50005, 'Payment amount must be greater than zero.', 1;

        IF @Paid + @Amount > @SaleAmount
            THROW 50006, 'Payment is greater than the amount still owed.', 1;

        INSERT INTO dbo.Payment
            (SaleID, Amount, PaymentMethod)
        VALUES
            (@SaleID, @Amount, @PaymentMethod);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

/* ============================================================
   This is a user defined procedure, used as a simple reusable sql for recording a collection after a sale
   ============================================================ */
CREATE PROCEDURE dbo.usp_RecordCollection
    @SaleID INT,
    @QuantityCollected DECIMAL(12,2),
    @CollectedBy VARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @TotalQuantity DECIMAL(12,2);
        DECLARE @Collected DECIMAL(12,2);

        SELECT @TotalQuantity = p.Quantity
        FROM dbo.Sale AS s
        INNER JOIN dbo.Produce AS p
            ON s.ProduceID = p.ProduceID
        WHERE s.SaleID = @SaleID;

        IF @TotalQuantity IS NULL
            THROW 50007, 'Sale was not found.', 1;

        SELECT @Collected = ISNULL(SUM(QuantityCollected), 0)
        FROM dbo.Collection
        WHERE SaleID = @SaleID;

        IF @QuantityCollected <= 0
            THROW 50008, 'Collection quantity must be greater than zero.', 1;

        IF @Collected + @QuantityCollected > @TotalQuantity
            THROW 50009, 'Collection is greater than the remaining quantity.', 1;

        INSERT INTO dbo.Collection
            (SaleID, QuantityCollected, CollectedBy)
        VALUES
            (@SaleID, @QuantityCollected, @CollectedBy);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

/* ============================================================
   This SQL codes creates an index in a drop down menu for all the produces from the farmers
   ============================================================ */
CREATE INDEX IX_Produce_Status
ON dbo.Produce(Status);
GO

CREATE INDEX IX_Bid_Produce_Amount
ON dbo.Bid(ProduceID, BidAmount DESC);
GO


CREATE INDEX IX_Payment_Sale
ON dbo.Payment(SaleID);
GO

CREATE INDEX IX_Collection_Sale
ON dbo.Collection(SaleID);
GO

/* ============================================================
   This SQL Code creates user roles for each system user, each system user has a unique role the play on the system 
   ============================================================ */
CREATE ROLE aa_readonly;
CREATE ROLE aa_depot;
CREATE ROLE aa_auction;
CREATE ROLE aa_finance;
GO

GRANT SELECT ON dbo.Farmer TO aa_readonly;
GRANT SELECT ON dbo.Buyer TO aa_readonly;
GRANT SELECT ON dbo.Produce TO aa_readonly;
GRANT SELECT ON dbo.Bid TO aa_readonly;
GRANT SELECT ON dbo.Sale TO aa_readonly;
GRANT SELECT ON dbo.Payment TO aa_readonly;
GRANT SELECT ON dbo.Collection TO aa_readonly;
GRANT SELECT ON dbo.vw_SalesPayments TO aa_readonly;
GRANT SELECT ON dbo.vw_Collections TO aa_readonly;
GRANT SELECT ON dbo.vw_AvailableProduce TO aa_readonly;
GRANT SELECT ON dbo.vw_AuctionResults TO aa_readonly;
GO

GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Farmer TO aa_depot;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Produce TO aa_depot;
GRANT EXECUTE ON dbo.usp_AddFarmer TO aa_depot;
GO

GRANT SELECT ON dbo.Buyer TO aa_auction;
GRANT SELECT, INSERT ON dbo.Bid TO aa_auction;
GRANT SELECT ON dbo.Produce TO aa_auction;
GRANT SELECT ON dbo.vw_AvailableProduce TO aa_auction;
GRANT SELECT ON dbo.vw_AuctionResults TO aa_auction;
GRANT EXECUTE ON dbo.usp_PlaceBid TO aa_auction;
GRANT EXECUTE ON dbo.usp_CloseAuction TO aa_auction;
GO

GRANT SELECT, INSERT ON dbo.Payment TO aa_finance;
GRANT SELECT ON dbo.Sale TO aa_finance;
GRANT SELECT ON dbo.Payment TO aa_finance;
GRANT SELECT ON dbo.vw_AuctionResults TO aa_finance;
GRANT SELECT ON dbo.vw_SalesPayments TO aa_finance;
GRANT EXECUTE ON dbo.usp_RecordPayment TO aa_finance;
GRANT SELECT, INSERT ON dbo.Collection TO aa_finance;
GRANT SELECT ON dbo.vw_Collections TO aa_finance;
GRANT EXECUTE ON dbo.usp_RecordCollection TO aa_finance;
GO

/* ============================================================
   This Sql code is some form of verification and testing code. It 
   checks that the database, tables, views, stored procedures, including indexes that have been created
    successfully and that data can be retrieved from the database itself.
   ============================================================ */
SELECT 'Database created successfully' AS Message;

SELECT * FROM dbo.Users;
SELECT * FROM dbo.Farmer;
SELECT * FROM dbo.Buyer;

SELECT * FROM dbo.vw_AvailableProduce;
SELECT * FROM dbo.vw_AuctionResults;
SELECT * FROM dbo.vw_SalesPayments;
SELECT * FROM dbo.vw_Collections;

SELECT name AS ProcedureName
FROM sys.procedures
WHERE name IN
(
    'usp_AddFarmer',
    'usp_PlaceBid',
    'usp_CloseAuction',
    'usp_RecordPayment',
    'usp_RecordCollection'
);

SELECT
    OBJECT_NAME(object_id) AS TableName,
    name AS IndexName
FROM sys.indexes
WHERE name IN
(
    'IX_Produce_Status',
    'IX_Bid_Produce_Amount'
);
GO
