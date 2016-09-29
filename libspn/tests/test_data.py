#!/usr/bin/env python3

# ------------------------------------------------------------------------
# Copyright (C) 2016 Andrzej Pronobis - All Rights Reserved
#
# This file is part of LibSPN. Unauthorized use or copying of this file,
# via any medium is strictly prohibited. Proprietary and confidential.
# ------------------------------------------------------------------------

import unittest
from unittest.mock import patch
import os
import tensorflow as tf
import numpy as np
from context import libspn as spn


class TestData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.realpath(os.path.join(os.getcwd(),
                                                     os.path.dirname(__file__),
                                                     "data"))

    def tearDown(self):
        tf.reset_default_graph()

    @patch.multiple(spn.FileDataset, __abstractmethods__=set())  # Make Dataset non-abstract
    def test_file_dataset_file_queue(self):
        """File queue of FileDataset"""
        # Glob
        dataset = spn.FileDataset(os.path.join(TestData.data_dir, "data_int*.csv"),
                                  num_epochs=1, batch_size=1, shuffle=False)
        fqueue = dataset._get_file_queue()
        files = []
        with spn.session() as (sess, run):
            while run():
                files.append(sess.run(fqueue.dequeue()))
        self.assertIn(files,
                      [[str.encode(os.path.join(TestData.data_dir, p))
                        for p in ["data_int1.csv", "data_int2.csv"]],
                       [str.encode(os.path.join(TestData.data_dir, p))
                        for p in ["data_int2.csv", "data_int1.csv"]]])

        # List of files
        dataset = spn.FileDataset([os.path.join(TestData.data_dir, p)
                                   for p in ["data_int1.csv", "data_int2.csv"]],
                                  num_epochs=1, batch_size=1, shuffle=False)
        fqueue = dataset._get_file_queue()
        files = []
        with spn.session() as (sess, run):
            while run():
                files.append(sess.run(fqueue.dequeue()))
        self.assertListEqual(files,
                             [str.encode(os.path.join(TestData.data_dir, p))
                              for p in ["data_int1.csv", "data_int2.csv"]])

        # One file
        dataset = spn.FileDataset(os.path.join(TestData.data_dir, "data_int1.csv"),
                                  num_epochs=1, batch_size=1, shuffle=False)
        fqueue = dataset._get_file_queue()
        files = []
        with spn.session() as (sess, run):
            while run():
                files.append(sess.run(fqueue.dequeue()))
        self.assertListEqual(files,
                             [str.encode(os.path.join(TestData.data_dir,
                                                      "data_int1.csv"))])

        # Glob, multiple epochs
        dataset = spn.FileDataset(os.path.join(TestData.data_dir, "data_int*.csv"),
                                  num_epochs=2, batch_size=1, shuffle=False)
        fqueue = dataset._get_file_queue()
        files = []
        with spn.session() as (sess, run):
            while run():
                files.append(sess.run(fqueue.dequeue()))
        self.assertIn(files,
                      [[str.encode(os.path.join(TestData.data_dir, p))
                        for p in ["data_int1.csv", "data_int2.csv",
                                  "data_int1.csv", "data_int2.csv"]],
                       [str.encode(os.path.join(TestData.data_dir, p))
                        for p in ["data_int2.csv", "data_int1.csv",
                                  "data_int2.csv", "data_int1.csv"]]])

        # List of files, multiple epochs
        dataset = spn.FileDataset([os.path.join(TestData.data_dir, p)
                                   for p in ["data_int1.csv", "data_int2.csv"]],
                                  num_epochs=2, batch_size=1, shuffle=False)
        fqueue = dataset._get_file_queue()
        files = []
        with spn.session() as (sess, run):
            while run():
                files.append(sess.run(fqueue.dequeue()))
        self.assertListEqual(files,
                             [str.encode(os.path.join(TestData.data_dir, p))
                              for p in ["data_int1.csv", "data_int2.csv",
                                        "data_int1.csv", "data_int2.csv"]])

    def generic_dataset_test(self, dataset, correct_batches):
        data = dataset.get_data()
        batches = []
        with spn.session() as (sess, run):
            while run():
                out = sess.run(data)
                batches.append(out)
        self.assertEqual(len(batches), len(correct_batches))
        for b, cb in zip(batches, correct_batches):
            if isinstance(b, list):
                self.assertEqual(len(b), len(cb))
                for bb, cbcb in zip(b, cb):
                    if cbcb is None:
                        self.assertIs(bb, None)
                    else:
                        np.testing.assert_array_equal(bb, cbcb)
            else:
                if cb is None:
                    self.assertIs(b, None)
                else:
                    np.testing.assert_array_equal(b, cb)

    def test_unlabeled_csv_file_dataset_without_final_batch(self):
        """Batch generation (without smaller final batch) for CSV file
        without labels"""
        # Note: shuffling is NOT tested
        dataset = spn.CSVFileDataset([os.path.join(TestData.data_dir, p)
                                      for p in ["data_int1.csv", "data_int2.csv"]],
                                     num_epochs=2,
                                     batch_size=3,
                                     shuffle=False,
                                     min_after_dequeue=1000,
                                     num_threads=1,
                                     allow_smaller_final_batch=False,
                                     num_labels=0,
                                     defaults=[[101], [102], [103], [104], [105]])
        batches = [np.array([[1, 2, 3, 4, 5],
                             [6, 102, 8, 9, 10],
                             [11, 12, 103, 14, 15]], dtype=np.int32),
                   np.array([[16, 102, 18, 19, 20],
                             [21, 22, 103, 24, 25],
                             [26, 27, 28, 104, 30]], dtype=np.int32),
                   np.array([[31, 32, 33, 104, 35],
                             [36, 37, 38, 104, 40],
                             [41, 42, 43, 104, 45]], dtype=np.int32),
                   np.array([[46, 47, 48, 104, 50],
                             [1, 2, 3, 4, 5],
                             [6, 102, 8, 9, 10]], dtype=np.int32),
                   np.array([[11, 12, 103, 14, 15],
                             [16, 102, 18, 19, 20],
                             [21, 22, 103, 24, 25]], dtype=np.int32),
                   np.array([[26, 27, 28, 104, 30],
                             [31, 32, 33, 104, 35],
                             [36, 37, 38, 104, 40]], dtype=np.int32)]
        self.generic_dataset_test(dataset, batches)

    def test_unlabeled_csv_file_dataset_with_final_batch(self):
        """Batch generation (without smaller final batch) for CSV file
        with labels"""
        # Note: shuffling is NOT tested
        dataset = spn.CSVFileDataset([os.path.join(TestData.data_dir, p)
                                      for p in ["data_int1.csv", "data_int2.csv"]],
                                     num_epochs=2,
                                     batch_size=3,
                                     shuffle=False,
                                     min_after_dequeue=1000,
                                     num_threads=1,
                                     allow_smaller_final_batch=True,
                                     num_labels=0,
                                     defaults=[[101], [102], [103], [104], [105]])
        batches = [np.array([[1, 2, 3, 4, 5],
                             [6, 102, 8, 9, 10],
                             [11, 12, 103, 14, 15]], dtype=np.int32),
                   np.array([[16, 102, 18, 19, 20],
                             [21, 22, 103, 24, 25],
                             [26, 27, 28, 104, 30]], dtype=np.int32),
                   np.array([[31, 32, 33, 104, 35],
                             [36, 37, 38, 104, 40],
                             [41, 42, 43, 104, 45]], dtype=np.int32),
                   np.array([[46, 47, 48, 104, 50],
                             [1, 2, 3, 4, 5],
                             [6, 102, 8, 9, 10]], dtype=np.int32),
                   np.array([[11, 12, 103, 14, 15],
                             [16, 102, 18, 19, 20],
                             [21, 22, 103, 24, 25]], dtype=np.int32),
                   np.array([[26, 27, 28, 104, 30],
                             [31, 32, 33, 104, 35],
                             [36, 37, 38, 104, 40]], dtype=np.int32),
                   np.array([[41, 42, 43, 104, 45],
                             [46, 47, 48, 104, 50]], dtype=np.int32)]
        self.generic_dataset_test(dataset, batches)

    def test_labeled_csv_file_dataset_int(self):
        """Batch generation for CSV file with integer data and 2 labels"""
        # Note: shuffling is NOT tested
        dataset = spn.CSVFileDataset([os.path.join(TestData.data_dir, p)
                                      for p in ["data_int1.csv", "data_int2.csv"]],
                                     num_epochs=2,
                                     batch_size=3,
                                     shuffle=False,
                                     min_after_dequeue=1000,
                                     num_threads=1,
                                     allow_smaller_final_batch=True,
                                     num_labels=2,
                                     defaults=[[101], [102], [103], [104], [105]])
        batches = [[np.array([[1, 2],
                              [6, 102],
                              [11, 12]], dtype=np.int32),
                    np.array([[3, 4, 5],
                              [8, 9, 10],
                              [103, 14, 15]], dtype=np.int32)],
                   [np.array([[16, 102],
                              [21, 22],
                              [26, 27]], dtype=np.int32),
                    np.array([[18, 19, 20],
                              [103, 24, 25],
                              [28, 104, 30]], dtype=np.int32)],
                   [np.array([[31, 32],
                              [36, 37],
                              [41, 42]], dtype=np.int32),
                    np.array([[33, 104, 35],
                              [38, 104, 40],
                              [43, 104, 45]], dtype=np.int32)],
                   [np.array([[46, 47],
                              [1, 2],
                              [6, 102]], dtype=np.int32),
                    np.array([[48, 104, 50],
                              [3, 4, 5],
                              [8, 9, 10]], dtype=np.int32)],
                   [np.array([[11, 12],
                              [16, 102],
                              [21, 22]], dtype=np.int32),
                    np.array([[103, 14, 15],
                              [18, 19, 20],
                              [103, 24, 25]], dtype=np.int32)],
                   [np.array([[26, 27],
                              [31, 32],
                              [36, 37]], dtype=np.int32),
                    np.array([[28, 104, 30],
                              [33, 104, 35],
                              [38, 104, 40]], dtype=np.int32)],
                   [np.array([[41, 42],
                              [46, 47]], dtype=np.int32),
                    np.array([[43, 104, 45],
                              [48, 104, 50]], dtype=np.int32)]]
        self.generic_dataset_test(dataset, batches)

    def test_labeled_csv_file_dataset_float(self):
        """Batch generation for CSV file with float data and 2 labels"""
        # Note: shuffling is NOT tested
        dataset = spn.CSVFileDataset(os.path.join(TestData.data_dir,
                                                  "data_mix.csv"),
                                     num_epochs=2,
                                     batch_size=3,
                                     shuffle=False,
                                     min_after_dequeue=1000,
                                     num_threads=1,
                                     allow_smaller_final_batch=True,
                                     num_labels=2,
                                     defaults=[[101.0], [102.0], [103.0], [104.0], [105.0]])
        batches = [[np.array([[1., 2.],
                              [6., 102.],
                              [11., 12.]], dtype=np.float32),
                    np.array([[3., 4., 5.],
                              [8., 104., 10.],
                              [103., 104., 15.]], dtype=np.float32)],
                   [np.array([[16., 102.],
                              [21., 22.],
                              [1., 2.]], dtype=np.float32),
                    np.array([[18., 19., 20.],
                              [103., 24., 25.],
                              [3., 4., 5.]], dtype=np.float32)],
                   [np.array([[6., 102.],
                              [11., 12.],
                              [16., 102.]], dtype=np.float32),
                    np.array([[8., 104., 10.],
                              [103., 104., 15.],
                              [18., 19., 20.]], dtype=np.float32)],
                   [np.array([[21., 22.]], dtype=np.float32),
                    np.array([[103., 24., 25.]], dtype=np.float32)]]
        self.generic_dataset_test(dataset, batches)

    def test_custom_csv_file_dataset(self):
        """Batch generation for CSV file with custom data"""
        class CustomCSVFileDataset(spn.CSVFileDataset):
            """Our custom dataset."""

            def process_data(self, data):
                return [data[0], tf.pack(data[1:3]), tf.pack(data[3:])]

        # Note: shuffling is NOT tested
        dataset = CustomCSVFileDataset(os.path.join(TestData.data_dir,
                                                    "data_mix.csv"),
                                       num_epochs=2,
                                       batch_size=3,
                                       shuffle=False,
                                       min_after_dequeue=1000,
                                       num_threads=1,
                                       allow_smaller_final_batch=True,
                                       num_labels=2,
                                       defaults=[[101.0], [102], [103], [104.0], [105.0]])
        batches = [[np.array([1., 6., 11.], dtype=np.float32),
                    np.array([[2, 3],
                              [102, 8],
                              [12, 103]], dtype=np.int32),
                    np.array([[4., 5.],
                              [104., 10.],
                              [104., 15.]], dtype=np.float32)],
                   [np.array([16., 21., 1.], dtype=np.float32),
                    np.array([[102, 18],
                              [22, 103],
                              [2, 3]], dtype=np.int32),
                    np.array([[19., 20.],
                              [24., 25.],
                              [4., 5.]], dtype=np.float32)],
                   [np.array([6., 11., 16.], dtype=np.float32),
                    np.array([[102, 8],
                              [12, 103],
                              [102, 18]], dtype=np.int32),
                    np.array([[104., 10.],
                              [104.,
                               15.],
                              [19., 20.]], dtype=np.float32)],
                   [np.array([21.], dtype=np.float32),
                    np.array([[22, 103]], dtype=np.int32),
                    np.array([[24., 25.]], dtype=np.float32)]]
        self.generic_dataset_test(dataset, batches)

    def test_gaussian_mixture_dataset_without_final(self):
        """Batch generation (without smaller final batch) for
        GaussianMixtureDataset"""
        # Tests: - normalization of weights,
        #        - components with and without labels
        # Note: shuffling is NOT tested
        components = [
            spn.GaussianMixtureDataset.Component(0.301, [1, 1], [[1, 0],
                                                                 [0, 1]]),
            spn.GaussianMixtureDataset.Component(0.2, [2, 2], [[1, 0],
                                                               [0, 1]], 10),
            spn.GaussianMixtureDataset.Component(0.2, [1, 1], [[1, 0],
                                                               [0, 1]])]
        dataset = spn.GaussianMixtureDataset(components=components,
                                             num_samples=100,
                                             num_epochs=2,
                                             batch_size=90,
                                             shuffle=False,
                                             num_threads=1,
                                             allow_smaller_final_batch=False)
        # Get batches
        data = dataset.get_data()
        batches = []
        with spn.session() as (sess, run):
            while run():
                out = sess.run(data)
                batches.append(out)

        # Num of batches
        self.assertEqual(len(batches), 2)

        # Batch size = 90
        batch1 = batches[0]
        batch2 = batches[1]
        self.assertTupleEqual(batch1[0].shape, (90, 2))  # samples
        self.assertTupleEqual(batch2[0].shape, (90, 2))
        self.assertTupleEqual(batch1[1].shape, (90, 1))  # labels
        self.assertTupleEqual(batch2[1].shape, (90, 1))
        self.assertTupleEqual(batch1[2].shape, (90, ))  # likelihoods
        self.assertTupleEqual(batch2[2].shape, (90, ))

        # Data type
        self.assertTrue(issubclass(batch1[0].dtype.type, np.float))
        self.assertTrue(issubclass(batch2[0].dtype.type, np.float))
        self.assertTrue(issubclass(batch1[1].dtype.type, np.integer))
        self.assertTrue(issubclass(batch2[1].dtype.type, np.integer))
        self.assertTrue(issubclass(batch1[2].dtype.type, np.float))
        self.assertTrue(issubclass(batch2[2].dtype.type, np.float))

        # Are the overlapping parts of the two batches identical?
        np.testing.assert_array_equal(batch1[0][:80], batch2[0][10:])
        np.testing.assert_array_equal(batch1[1][:80], batch2[1][10:])
        np.testing.assert_array_equal(batch1[2][:80], batch2[2][10:])

        # Number of samples per component
        epoch_labels = np.concatenate([batch1[1], batch2[1][:10]])
        self.assertEqual((epoch_labels == 0).sum(), 43)
        self.assertEqual((epoch_labels == 10).sum(), 28)
        self.assertEqual((epoch_labels == 2).sum(), 29)   # Roundoff error

    def test_gaussian_mixture_dataset_with_final(self):
        """Batch generation (with smaller final batch) for
        GaussianMixtureDataset"""
        # Tests: - normalization of weights,
        #        - components with and without labels
        # Note: shuffling is NOT tested
        components = [
            spn.GaussianMixtureDataset.Component(0.301, [1, 1], [[1, 0],
                                                                 [0, 1]]),
            spn.GaussianMixtureDataset.Component(0.2, [2, 2], [[1, 0],
                                                               [0, 1]], 10),
            spn.GaussianMixtureDataset.Component(0.2, [1, 1], [[1, 0],
                                                               [0, 1]])]
        dataset = spn.GaussianMixtureDataset(components=components,
                                             num_samples=100,
                                             num_epochs=2,
                                             batch_size=90,
                                             shuffle=False,
                                             num_threads=1,
                                             allow_smaller_final_batch=True)
        # Get batches
        data = dataset.get_data()
        batches = []
        with spn.session() as (sess, run):
            while run():
                out = sess.run(data)
                batches.append(out)

        # Num of batches
        self.assertEqual(len(batches), 3)

        # Batch size = 90
        batch1 = batches[0]
        batch2 = batches[1]
        batch3 = batches[2]
        self.assertTupleEqual(batch1[0].shape, (90, 2))  # samples
        self.assertTupleEqual(batch2[0].shape, (90, 2))
        self.assertTupleEqual(batch3[0].shape, (20, 2))
        self.assertTupleEqual(batch1[1].shape, (90, 1))  # labels
        self.assertTupleEqual(batch2[1].shape, (90, 1))
        self.assertTupleEqual(batch3[1].shape, (20, 1))
        self.assertTupleEqual(batch1[2].shape, (90, ))  # likelihoods
        self.assertTupleEqual(batch2[2].shape, (90, ))
        self.assertTupleEqual(batch3[2].shape, (20, ))

        # Data type
        self.assertTrue(issubclass(batch1[0].dtype.type, np.float))
        self.assertTrue(issubclass(batch2[0].dtype.type, np.float))
        self.assertTrue(issubclass(batch3[0].dtype.type, np.float))
        self.assertTrue(issubclass(batch1[1].dtype.type, np.integer))
        self.assertTrue(issubclass(batch2[1].dtype.type, np.integer))
        self.assertTrue(issubclass(batch3[1].dtype.type, np.integer))
        self.assertTrue(issubclass(batch1[2].dtype.type, np.float))
        self.assertTrue(issubclass(batch2[2].dtype.type, np.float))
        self.assertTrue(issubclass(batch3[2].dtype.type, np.float))

        # Are the overlapping parts of the batches identical?
        np.testing.assert_array_equal(batch1[0][:80], batch2[0][10:])
        np.testing.assert_array_equal(np.concatenate([batch1[0][80:],
                                                      batch2[0][:10]]),
                                      batch3[0])
        np.testing.assert_array_equal(batch1[1][:80], batch2[1][10:])
        np.testing.assert_array_equal(np.concatenate([batch1[1][80:],
                                                      batch2[1][:10]]),
                                      batch3[1])
        np.testing.assert_array_equal(batch1[2][:80], batch2[2][10:])
        np.testing.assert_array_equal(np.concatenate([batch1[2][80:],
                                                      batch2[2][:10]]),
                                      batch3[2])

        # Number of samples per component
        epoch_labels = np.concatenate([batch1[1], batch2[1][:10]])
        self.assertEqual((epoch_labels == 0).sum(), 43)
        self.assertEqual((epoch_labels == 10).sum(), 28)
        self.assertEqual((epoch_labels == 2).sum(), 29)  # Roundoff error

    def test_discrete_gaussian_mixture_dataset_with_final(self):
        """Batch generation (with smaller final batch) for
        GaussianMixtureDataset with digitization"""
        # Tests: - normalization of weights,
        #        - components with and without labels
        # Note: shuffling is NOT tested
        components = [
            spn.GaussianMixtureDataset.Component(0.301, [1, 1], [[1, 0],
                                                                 [0, 1]]),
            spn.GaussianMixtureDataset.Component(0.2, [2, 2], [[1, 0],
                                                               [0, 1]], 10),
            spn.GaussianMixtureDataset.Component(0.2, [1, 1], [[1, 0],
                                                               [0, 1]])]
        dataset = spn.GaussianMixtureDataset(components=components,
                                             num_samples=100,
                                             num_epochs=2,
                                             batch_size=90,
                                             shuffle=False,
                                             num_threads=1,
                                             allow_smaller_final_batch=True,
                                             num_vals=10)
        # Get batches
        data = dataset.get_data()
        batches = []
        with spn.session() as (sess, run):
            while run():
                out = sess.run(data)
                batches.append(out)

        # Num of batches
        self.assertEqual(len(batches), 3)

        # Batch size = 90
        batch1 = batches[0]
        batch2 = batches[1]
        batch3 = batches[2]
        self.assertTupleEqual(batch1[0].shape, (90, 2))  # samples
        self.assertTupleEqual(batch2[0].shape, (90, 2))
        self.assertTupleEqual(batch3[0].shape, (20, 2))
        self.assertTupleEqual(batch1[1].shape, (90, 1))  # labels
        self.assertTupleEqual(batch2[1].shape, (90, 1))
        self.assertTupleEqual(batch3[1].shape, (20, 1))
        self.assertTupleEqual(batch1[2].shape, (90, ))  # likelihoods
        self.assertTupleEqual(batch2[2].shape, (90, ))
        self.assertTupleEqual(batch3[2].shape, (20, ))

        # Data type
        self.assertTrue(issubclass(batch1[0].dtype.type, np.integer))
        self.assertTrue(issubclass(batch2[0].dtype.type, np.integer))
        self.assertTrue(issubclass(batch3[0].dtype.type, np.integer))
        self.assertTrue(issubclass(batch1[1].dtype.type, np.integer))
        self.assertTrue(issubclass(batch2[1].dtype.type, np.integer))
        self.assertTrue(issubclass(batch3[1].dtype.type, np.integer))
        self.assertTrue(issubclass(batch1[2].dtype.type, np.float))
        self.assertTrue(issubclass(batch2[2].dtype.type, np.float))
        self.assertTrue(issubclass(batch3[2].dtype.type, np.float))

        # Are the overlapping parts of the batches identical?
        np.testing.assert_array_equal(batch1[0][:80], batch2[0][10:])
        np.testing.assert_array_equal(np.concatenate([batch1[0][80:],
                                                      batch2[0][:10]]),
                                      batch3[0])
        np.testing.assert_array_equal(batch1[1][:80], batch2[1][10:])
        np.testing.assert_array_equal(np.concatenate([batch1[1][80:],
                                                      batch2[1][:10]]),
                                      batch3[1])
        np.testing.assert_array_equal(batch1[2][:80], batch2[2][10:])
        np.testing.assert_array_equal(np.concatenate([batch1[2][80:],
                                                      batch2[2][:10]]),
                                      batch3[2])

        # Number of samples per component
        epoch_labels = np.concatenate([batch1[1], batch2[1][:10]])
        self.assertEqual((epoch_labels == 0).sum(), 43)
        self.assertEqual((epoch_labels == 10).sum(), 28)
        self.assertEqual((epoch_labels == 2).sum(), 29)  # Roundoff error

        # Are values within range?
        epoch_samples = np.concatenate([batch1[0], batch2[0][:10]])
        self.assertEqual(epoch_samples.min(), 0)
        self.assertEqual(epoch_samples.max(), 9)

    def test_read_all_labeled_csv_file_dataset(self):
        """Test read_all for CSV file with 2 labels."""
        dataset = spn.CSVFileDataset([os.path.join(TestData.data_dir, p)
                                      for p in ["data_int1.csv", "data_int2.csv"]],
                                     num_epochs=2,
                                     batch_size=3,
                                     shuffle=False,
                                     min_after_dequeue=1000,
                                     num_threads=1,
                                     allow_smaller_final_batch=True,
                                     num_labels=2,
                                     defaults=[[101], [102], [103], [104], [105]])
        data = dataset.read_all()
        self.assertEqual(len(data), 2)
        np.testing.assert_array_equal(data[0],
                                      np.array([[1, 2],
                                                [6, 102],
                                                [11, 12],
                                                [16, 102],
                                                [21, 22],
                                                [26, 27],
                                                [31, 32],
                                                [36, 37],
                                                [41, 42],
                                                [46, 47],
                                                [1, 2],
                                                [6, 102],
                                                [11, 12],
                                                [16, 102],
                                                [21, 22],
                                                [26, 27],
                                                [31, 32],
                                                [36, 37],
                                                [41, 42],
                                                [46, 47]], dtype=np.int32))
        np.testing.assert_array_equal(data[1],
                                      np.array([[3, 4, 5],
                                                [8, 9, 10],
                                                [103, 14, 15],
                                                [18, 19, 20],
                                                [103, 24, 25],
                                                [28, 104, 30],
                                                [33, 104, 35],
                                                [38, 104, 40],
                                                [43, 104, 45],
                                                [48, 104, 50],
                                                [3, 4, 5],
                                                [8, 9, 10],
                                                [103, 14, 15],
                                                [18, 19, 20],
                                                [103, 24, 25],
                                                [28, 104, 30],
                                                [33, 104, 35],
                                                [38, 104, 40],
                                                [43, 104, 45],
                                                [48, 104, 50]], dtype=np.int32))

    def test_read_all_int_grid_dataset(self):
        dataset = spn.IntGridDataset(num_dims=2,
                                     num_vals=3,
                                     num_epochs=2,
                                     batch_size=4,
                                     shuffle=False,
                                     num_threads=1,
                                     allow_smaller_final_batch=True)
        data = dataset.read_all()

        np.testing.assert_array_equal(data, np.array([[0, 0],
                                                      [0, 1],
                                                      [0, 2],
                                                      [1, 0],
                                                      [1, 1],
                                                      [1, 2],
                                                      [2, 0],
                                                      [2, 1],
                                                      [2, 2],
                                                      [0, 0],
                                                      [0, 1],
                                                      [0, 2],
                                                      [1, 0],
                                                      [1, 1],
                                                      [1, 2],
                                                      [2, 0],
                                                      [2, 1],
                                                      [2, 2]], dtype=np.int32))

    def test_write_all_single_tensor(self):
        path = os.path.join(TestData.data_dir, "out_test_write_all_single_tensor.csv")

        # Read&write
        dataset = spn.CSVFileDataset(os.path.join(TestData.data_dir, "data_int1.csv"),
                                     num_epochs=2,
                                     batch_size=4,
                                     shuffle=False,
                                     min_after_dequeue=1000,
                                     num_threads=1,
                                     allow_smaller_final_batch=True,
                                     num_labels=0,
                                     defaults=[[101], [102], [103], [104], [105]])
        writer = spn.CSVDataWriter(path)
        data1 = dataset.read_all()
        dataset.write_all(writer)

        # Read again
        dataset = spn.CSVFileDataset(path,
                                     num_epochs=1,
                                     batch_size=4,
                                     shuffle=False,
                                     min_after_dequeue=1000,
                                     num_threads=1,
                                     allow_smaller_final_batch=True,
                                     num_labels=0,
                                     defaults=[[201], [202], [203], [204], [205]])
        data2 = dataset.read_all()

        # Compare
        np.testing.assert_array_equal(data1, data2)

    def test_write_all_tensor_list(self):
        path = os.path.join(TestData.data_dir, "out_test_write_all_tensor_list.csv")

        # Read&write
        dataset = spn.CSVFileDataset(os.path.join(TestData.data_dir, "data_int1.csv"),
                                     num_epochs=2,
                                     batch_size=4,
                                     shuffle=False,
                                     min_after_dequeue=1000,
                                     num_threads=1,
                                     allow_smaller_final_batch=True,
                                     num_labels=2,
                                     defaults=[[101], [102], [103.0], [104.0], [105.0]])
        writer = spn.CSVDataWriter(path)
        data1 = dataset.read_all()
        dataset.write_all(writer)

        # Read again
        dataset = spn.CSVFileDataset(path,
                                     num_epochs=1,
                                     batch_size=4,
                                     shuffle=False,
                                     min_after_dequeue=1000,
                                     num_threads=1,
                                     allow_smaller_final_batch=True,
                                     num_labels=2,
                                     defaults=[[201], [202], [203.0], [204.0], [205.0]])
        data2 = dataset.read_all()

        # Compare
        np.testing.assert_array_equal(data1[0], data2[0])
        np.testing.assert_array_almost_equal(data1[1], data2[1])

    def test_csv_data_writer(self):
        # Write
        path = os.path.join(TestData.data_dir, "out_test_csv_data_writer.csv")
        writer = spn.CSVDataWriter(path)

        arr1 = np.array([1, 2, 3, 4])
        arr2 = np.array([[1 / 1, 1 / 2],
                         [1 / 3, 1 / 4],
                         [1 / 5, 1 / 6],
                         [1 / 7, 1 / 8]])
        writer.write((arr1, arr2))
        writer.write((arr1, arr2))

        # Read
        dataset = spn.CSVFileDataset(path,
                                     num_epochs=1,
                                     batch_size=10,
                                     shuffle=False,
                                     min_after_dequeue=1000,
                                     num_threads=1,
                                     allow_smaller_final_batch=True,
                                     num_labels=1,
                                     defaults=[[1], [1.0], [1.0]])
        data = dataset.read_all()

        # Compare
        np.testing.assert_array_equal(np.concatenate((arr1, arr1)),
                                      data[0].flatten())
        np.testing.assert_array_almost_equal(np.concatenate((arr2, arr2)),
                                             data[1])


if __name__ == '__main__':
    unittest.main()